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

        logger.info(f"RAG query received: {query[:100]}... (session: {session_id})")

        # Retrieve relevant documents
        context = ""
        sources = []
        if self.vector_store and self.embedding_gen:
            try:
                # Generate query embedding
                logger.debug("Generating query embedding...")
                query_embedding = self.embedding_gen.generate([query])[0]
                logger.debug(f"Query embedding dimension: {len(query_embedding)}")
                
                # Search vector store
                logger.debug("Searching vector store...")
                results = self.vector_store.query(query_embedding, top_k=5)
                logger.info(f"Retrieved {len(results)} results from vector store")
                
                # Build context
                context_parts = []
                for i, result in enumerate(results):
                    metadata = result.get("metadata", {})
                    text = metadata.get("text", "")
                    score = result.get("score", 0.0)
                    chunk_id = result.get("id", "")
                    filename = metadata.get("filename", "Unknown")
                    
                    logger.debug(
                        f"Result {i+1}: score={score:.3f}, "
                        f"filename={filename}, text_length={len(text)}"
                    )
                    
                    if text and text.strip():
                        context_parts.append(text)
                        sources.append(f"{filename} (chunk: {chunk_id})")
                
                context = "\n\n".join(context_parts)
                logger.info(
                    f"Built context from {len(context_parts)} chunks "
                    f"(total length: {len(context)} chars)"
                )
            except Exception as e:
                logger.error(f"Error in RAG retrieval: {e}", exc_info=True)
        else:
            logger.warning("Vector store or embedding generator not available")

        # Build prompt with context - optimized for Gemini
        if context:
            # Shorter, more structured format for Gemini
            enhanced_query = f"Context:\n{context}\n\nQ: {query}\nA:"
            logger.debug(f"Enhanced query length: {len(enhanced_query)} chars")
        else:
            enhanced_query = f"Q: {query}\nA:"
            logger.warning("No context available for query")

        input_data["query"] = enhanced_query
        result = super().act(input_data)

        # Add sources
        result["sources"] = sources
        logger.info(f"RAG response generated with {len(sources)} sources")

        return result

