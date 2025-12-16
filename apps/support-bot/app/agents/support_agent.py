"""Support bot agents.

This module defines a small agent hierarchy:
- IntentClassifierAgent: classifies user intent (billing, technical, general)
- AnswerAgent: RAG-based answering using PGVector
- EscalationAgent: decides whether to escalate and creates tickets via tools
- SupportAgent: orchestrates the three agents to produce a single response
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from core.agents import BaseAgent
from core.embeddings import EmbeddingGenerator, EmbeddingsStore
from core.llm import LLM
from core.memory import RedisSessionMemory
from core.tools import ToolRegistry

from ..models.support_models import Intent, TicketPriority


def simple_intent_classifier(message: str) -> Intent:
    """Lightweight, deterministic intent classifier.

    This provides a baseline classification that is cheap and works in tests
    without requiring LLM calls.
    """
    lower = message.lower()
    billing_keywords = ["invoice", "billing", "charge", "refund", "payment", "price"]
    technical_keywords = ["error", "bug", "issue", "crash", "install", "login", "timeout"]

    if any(k in lower for k in billing_keywords):
        return Intent.BILLING
    if any(k in lower for k in technical_keywords):
        return Intent.TECHNICAL
    return Intent.GENERAL


class IntentClassifierAgent(BaseAgent):
    """Agent that classifies the user's intent."""

    def act(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        message = input_data.get("query", "")
        session_id = input_data.get("session_id", "default")

        # Start with deterministic classifier
        intent = simple_intent_classifier(message)

        # Optionally refine with LLM in the future; for now deterministic is enough
        if self.memory:
            self.memory.append_message(session_id, "user", message, {"intent": intent.value})

        logger.info(f"Classified intent as {intent.value}")
        return {"intent": intent.value}


class AnswerAgent(BaseAgent):
    """RAG-based answer agent using PGVector."""

    def __init__(
        self,
        *args: Any,
        vector_store: Optional[EmbeddingsStore] = None,
        embedding_gen: Optional[EmbeddingGenerator] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.vector_store = vector_store
        self.embedding_gen = embedding_gen

    def get_system_prompt(self) -> str:
        return (
            "You are a customer support assistant. Use the provided context to answer "
            "customer questions accurately. If the context is insufficient, clearly "
            'say so and suggest escalation to a human agent. Be concise and helpful.'
        )

    def _build_context(self, query: str) -> Tuple[str, List[str], float]:
        """Retrieve context from the vector store and compute a retrieval score."""
        if not self.vector_store or not self.embedding_gen:
            logger.warning("Vector store or embedding generator is not configured")
            return "", [], 0.0

        try:
            query_embedding = self.embedding_gen.generate([query])[0]
            results = self.vector_store.query(query_embedding, top_k=5)
        except Exception as exc:
            logger.error(f"RAG retrieval failed: {exc}", exc_info=True)
            return "", [], 0.0

        context_parts: List[str] = []
        sources: List[str] = []
        top_similarity = 0.0

        for result in results:
            metadata = result.get("metadata") or {}
            text = metadata.get("text", "")
            score = float(result.get("score", 0.0))
            top_similarity = max(top_similarity, score)

            if not text or not text.strip():
                continue

            filename = metadata.get("filename", "unknown")
            chunk_id = metadata.get("chunk_id") or result.get("id", "")

            context_parts.append(text)
            sources.append(f"{filename} (chunk: {chunk_id})")

        context = "\n\n".join(context_parts)
        logger.info(
            f"Built context with {len(context_parts)} chunks, top_similarity={top_similarity:.3f}"
        )
        return context, sources, top_similarity

    def _self_evaluate(
        self, question: str, answer: str, context: str, base_score: float
    ) -> float:
        """Ask the LLM to self-evaluate confidence on a [0,1] scale."""
        prompt = (
            "You are evaluating your own answer to a customer.\n"
            f"Question: {question}\n\n"
            f"Context used:\n{context or 'NO CONTEXT AVAILABLE'}\n\n"
            f"Answer you gave:\n{answer}\n\n"
            "On a scale from 0 to 1, where 0 means 'not confident at all' and 1 means "
            "'very confident and fully supported by the context', output only a single "
            "floating point number. Do not include any explanation.\n"
            f"Base retrieval score (0-1) was: {base_score:.3f}"
        )

        try:
            score_text = self.llm.chat(prompt).strip()
            value = float(score_text.split()[0])
        except Exception as exc:
            logger.error(f"Self-evaluation failed: {exc}")
            # Fallback: use retrieval score as a proxy
            value = base_score

        value = max(0.0, min(1.0, value))
        logger.info(f"LLM self-evaluation confidence={value:.3f}")
        return value

    def act(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        message = input_data.get("query", "")
        session_id = input_data.get("session_id", "default")

        context, sources, retrieval_conf = self._build_context(message)

        system_prompt = self.get_system_prompt()
        prompt_parts = [system_prompt]

        if self.memory:
            history = self.memory.get_messages(session_id)
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    prompt_parts.append(f"User: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Assistant: {content}")

        if context:
            prompt_parts.append(f"Context:\n{context}")
        prompt_parts.append(f"User: {message}")

        prompt = "\n\n".join(prompt_parts)
        logger.debug(f"AnswerAgent prompt length={len(prompt)}")

        answer = self.llm.chat(prompt)
        self_eval_conf = self._self_evaluate(message, answer, context, retrieval_conf)

        # Combine retrieval and self-eval confidence (simple average)
        confidence = (retrieval_conf + self_eval_conf) / 2.0
        logger.info(
            f"AnswerAgent: retrieval_conf={retrieval_conf:.3f}, "
            f"self_eval_conf={self_eval_conf:.3f}, combined={confidence:.3f}"
        )

        if self.memory:
            self.memory.append_message(session_id, "user", message)
            self.memory.append_message(
                session_id,
                "assistant",
                answer,
                {"confidence": confidence, "retrieval_conf": retrieval_conf},
            )

        return {
            "response": answer,
            "sources": sources,
            "retrieval_confidence": retrieval_conf,
            "self_eval_confidence": self_eval_conf,
            "confidence": confidence,
        }


class EscalationAgent(BaseAgent):
    """Agent that decides on escalation and creates tickets via tools."""

    def __init__(
        self,
        *args: Any,
        tools: Optional[ToolRegistry] = None,
        threshold: float = 0.65,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, tools=tools, **kwargs)
        self.threshold = threshold

    def act(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        confidence: float = float(input_data.get("confidence", 0.0))
        intent_str: str = (input_data.get("intent") or Intent.GENERAL.value).lower()
        message: str = input_data.get("query", "")
        answer: str = input_data.get("answer", "")
        session_id: str = input_data.get("session_id", "default")
        user_id: Optional[str] = input_data.get("user_id")

        if confidence >= self.threshold:
            logger.info(
                f"No escalation needed (confidence={confidence:.3f}, "
                f"threshold={self.threshold:.3f})"
            )
            return {"escalated": False, "ticket_id": None}

        logger.info(
            f"Escalating conversation (confidence={confidence:.3f} < "
            f"threshold={self.threshold:.3f})"
        )

        # Derive a simple subject/description for the ticket
        subject = f"{intent_str.title()} support request"
        description = (
            f"User message:\n{message}\n\n"
            f"AI answer (low confidence {confidence:.2f}):\n{answer}\n"
        )

        ticket_payload = {
            "subject": subject,
            "description": description,
            "intent": intent_str,
            "priority": TicketPriority.HIGH.value
            if intent_str == Intent.BILLING.value
            else TicketPriority.MEDIUM.value,
            "session_id": session_id,
            "user_id": user_id,
        }

        ticket_id: Optional[str] = None
        if self.tools:
            try:
                result = self.tools.execute("create_support_ticket", ticket_payload)
                if result.get("success", True):
                    ticket_id = result.get("ticket_id")
            except Exception as exc:
                logger.error(f"Failed to create ticket via tool: {exc}", exc_info=True)

        if self.memory:
            self.memory.append_message(
                session_id,
                "system",
                f"Conversation escalated to human (ticket_id={ticket_id})",
                {"ticket_id": ticket_id, "confidence": confidence},
            )

        return {"escalated": True, "ticket_id": ticket_id}


class SupportAgent(BaseAgent):
    """High-level orchestrator for the support bot."""

    def __init__(
        self,
        name: str,
        llm: LLM,
        memory: RedisSessionMemory,
        vector_store: Optional[EmbeddingsStore],
        embedding_gen: Optional[EmbeddingGenerator],
        tools: ToolRegistry,
        escalation_threshold: float = 0.65,
    ) -> None:
        super().__init__(name=name, llm=llm, memory=memory, tools=tools)

        self.intent_agent = IntentClassifierAgent(
            name="intent-classifier",
            llm=llm,
            memory=memory,
            tools=tools,
        )
        self.answer_agent = AnswerAgent(
            name="answer-agent",
            llm=llm,
            memory=memory,
            tools=tools,
            vector_store=vector_store,
            embedding_gen=embedding_gen,
        )
        self.escalation_agent = EscalationAgent(
            name="escalation-agent",
            llm=llm,
            memory=memory,
            tools=tools,
            threshold=escalation_threshold,
        )

    def act(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the full pipeline: classify → answer → maybe escalate."""
        message = input_data.get("query", "")
        session_id = input_data.get("session_id", "default")
        user_id: Optional[str] = input_data.get("user_id")

        logger.info(f"SupportAgent handling message (session={session_id})")

        intent_result = self.intent_agent.act(
            {"query": message, "session_id": session_id}
        )
        intent = Intent(intent_result.get("intent", Intent.GENERAL.value))

        answer_result = self.answer_agent.act(
            {"query": message, "session_id": session_id}
        )
        confidence = float(answer_result.get("confidence", 0.0))

        escalation_result = self.escalation_agent.act(
            {
                "intent": intent.value,
                "confidence": confidence,
                "query": message,
                "answer": answer_result.get("response", ""),
                "session_id": session_id,
                "user_id": user_id,
            }
        )

        return {
            "response": answer_result.get("response", ""),
            "intent": intent.value,
            "confidence": confidence,
            "escalated": escalation_result.get("escalated", False),
            "ticket_id": escalation_result.get("ticket_id"),
            "sources": answer_result.get("sources", []),
        }


