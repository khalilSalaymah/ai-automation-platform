"""RAG agent implementation."""

from typing import Dict, Any, Optional
from core.agents import ToolExecutionAgent
from core.embeddings import EmbeddingsStore, EmbeddingGenerator
from core.logger import logger


class RAGAgent(ToolExecutionAgent):
    """RAG agent with document retrieval."""

    def __init__(
        self,
        *args,
        vector_store: Optional[EmbeddingsStore] = None,
        embedding_gen: Optional[EmbeddingGenerator] = None,
        **kwargs
    ):
        """Initialize RAG agent."""
        super().__init__(*args, **kwargs)
        self.vector_store = vector_store
        self.embedding_gen = embedding_gen

    def get_system_prompt(self) -> str:
        """Get system prompt for RAG agent."""
        # Optimized for Gemini: clear, structured instructions
        return """RAG assistant. Answer using provided context.
- Use context when available
- Cite sources
- Say "not in context" if missing
- Be accurate and concise"""

    def act(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process query with RAG."""
        query = input_data.get("query", "")
        session_id = input_data.get("session_id", "default")

        # Retrieve relevant documents
        context = ""
        sources = []
        if self.vector_store and self.embedding_gen:
            try:
                # Generate query embedding
                query_embedding = self.embedding_gen.generate([query])[0]
                
                # Search vector store
                results = self.vector_store.query(query_embedding, top_k=5)
                
                # Build context
                context_parts = []
                for result in results:
                    context_parts.append(result.get("metadata", {}).get("text", ""))
                    sources.append(result.get("id", ""))
                
                context = "\n\n".join(context_parts)
            except Exception as e:
                logger.error(f"Error in RAG retrieval: {e}")

        # Build prompt with context - optimized for Gemini
        if context:
            # Shorter, more structured format for Gemini
            enhanced_query = f"Context:\n{context}\n\nQ: {query}\nA:"
        else:
            enhanced_query = f"Q: {query}\nA:"

        input_data["query"] = enhanced_query
        result = super().act(input_data)

        # Add sources
        result["sources"] = sources

        return result

