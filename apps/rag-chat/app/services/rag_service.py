"""RAG service business logic."""

from typing import List, Optional
from core.logger import logger
from core import LLM, RedisSessionMemory, EmbeddingGenerator
from core.vectorstore import PGVectorStore, PineconeStore
from core.config import get_settings

from ..agents.rag_agent import RAGAgent
from ..models.rag_models import ChatRequest, ChatResponse, DocumentInfo
from ..config import settings

settings_core = get_settings()


class RAGService:
    """RAG processing service."""

    def __init__(self):
        """Initialize RAG service."""
        # LLM will auto-detect provider from LLM_PROVIDER env var
        # For RAG chat, set LLM_PROVIDER=gemini and GEMINI_API_KEY
        self.llm = LLM(model="gemini-1.5-flash")
        self.memory = RedisSessionMemory(url=settings.redis_url)
        # EmbeddingGenerator uses Gemini embeddings (same API key as LLM)
        # GEMINI_API_KEY is loaded from environment automatically
        self.embedding_gen = EmbeddingGenerator()

        # Initialize vector store
        if settings.vector_store == "pinecone" and settings.pinecone_api_key:
            self.vector_store = PineconeStore(
                api_key=settings.pinecone_api_key,
                index_name=settings.pinecone_index or "rag-chat",
                environment=settings.pinecone_environment,
            )
        else:
            self.vector_store = PGVectorStore(
                uri=settings.database_url,
                table_name="rag_documents",
            )

        self.agent = RAGAgent(
            name="rag-agent",
            llm=self.llm,
            memory=self.memory,
            vector_store=self.vector_store,
            embedding_gen=self.embedding_gen,
        )

    async def chat(self, message: str, session_id: Optional[str] = None) -> ChatResponse:
        """Chat with RAG."""
        try:
            result = self.agent.act({
                "query": message,
                "session_id": session_id or "default",
            })
            return ChatResponse(
                response=result.get("response", ""),
                sources=result.get("sources", []),
            )
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            raise

    async def index_document(self, filename: str, content: bytes) -> str:
        """Index a document."""
        try:
            import uuid
            doc_id = str(uuid.uuid4())
            text = content.decode("utf-8")

            # Generate embedding
            embeddings = self.embedding_gen.generate([text])
            
            # Store in vector store
            self.vector_store.add(
                vectors=embeddings,
                metadata=[{"filename": filename, "doc_id": doc_id}],
                ids=[doc_id],
            )

            return doc_id
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            raise

    async def list_documents(self) -> List[DocumentInfo]:
        """List indexed documents."""
        # Implementation would query database
        return []

