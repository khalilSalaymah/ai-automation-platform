"""RAG service business logic."""

from typing import List, Optional
from datetime import datetime
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
        # LLM will auto-detect provider from LLM_PROVIDER env var.
        # For RAG chat with Gemini, set LLM_PROVIDER=gemini and GEMINI_API_KEY.
        # We rely on the LLM wrapper's default Gemini model (currently gemini-pro)
        # instead of hard-coding a specific model that may not be available for
        # the configured API version.
        self.llm = LLM()
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
            import io
            doc_id = str(uuid.uuid4())
            
            logger.info(f"Indexing document: {filename} (size: {len(content)} bytes)")
            
            # Extract text based on file type
            text = ""
            if filename.lower().endswith('.pdf'):
                try:
                    import PyPDF2
                    logger.info(f"Extracting text from PDF: {filename}")
                    pdf_file = io.BytesIO(content)
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text_parts = []
                    for i, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        text_parts.append(page_text)
                        logger.debug(f"Extracted {len(page_text)} chars from page {i+1}")
                    text = "\n\n".join(text_parts)
                    logger.info(f"Extracted {len(text)} total characters from PDF")
                except Exception as e:
                    logger.error(f"Failed to extract PDF text: {e}")
                    raise ValueError(f"Failed to parse PDF: {e}") from e
            elif filename.lower().endswith(('.doc', '.docx')):
                try:
                    from docx import Document
                    logger.info(f"Extracting text from DOCX: {filename}")
                    doc_file = io.BytesIO(content)
                    doc = Document(doc_file)
                    text_parts = []
                    for para in doc.paragraphs:
                        text_parts.append(para.text)
                    text = "\n\n".join(text_parts)
                    logger.info(f"Extracted {len(text)} characters from DOCX")
                except Exception as e:
                    logger.error(f"Failed to extract DOCX text: {e}")
                    raise ValueError(f"Failed to parse DOCX: {e}") from e
            else:
                # Try to decode as UTF-8 text file
                try:
                    text = content.decode("utf-8")
                    logger.info(f"Decoded {len(text)} characters as UTF-8 text")
                except UnicodeDecodeError:
                    # Fallback: decode with errors ignored
                    text = content.decode("utf-8", errors="ignore")
                    logger.warning(f"Decoded text with errors ignored, got {len(text)} characters")

            if not text or len(text.strip()) == 0:
                raise ValueError(f"No text could be extracted from {filename}")

            # Split into chunks for better retrieval (chunks of ~1000 chars with overlap)
            chunk_size = 1000
            chunk_overlap = 200
            chunks = []
            chunk_ids = []
            
            for i in range(0, len(text), chunk_size - chunk_overlap):
                chunk = text[i:i + chunk_size]
                if chunk.strip():
                    chunks.append(chunk)
                    chunk_ids.append(f"{doc_id}_chunk_{len(chunk_ids)}")
            
            logger.info(f"Split document into {len(chunks)} chunks")
            
            if not chunks:
                raise ValueError(f"No valid chunks created from {filename}")

            # Generate embeddings for all chunks
            logger.info(f"Generating embeddings for {len(chunks)} chunks...")
            embeddings = self.embedding_gen.generate(chunks)
            logger.info(f"Generated {len(embeddings)} embeddings (dim: {len(embeddings[0]) if embeddings else 0})")

            # Prepare metadata for each chunk
            metadata_list = []
            for i, chunk in enumerate(chunks):
                metadata_list.append({
                    "filename": filename,
                    "doc_id": doc_id,
                    "chunk_id": chunk_ids[i],
                    "chunk_index": i,
                    "text": chunk,
                    "total_chunks": len(chunks)
                })

            # Store in vector store
            logger.info(f"Storing {len(embeddings)} vectors in vector store...")
            self.vector_store.add(
                vectors=embeddings,
                metadata=metadata_list,
                ids=chunk_ids,
            )
            logger.info(f"Successfully indexed document {filename} with {len(chunks)} chunks")

            return doc_id
        except Exception as e:
            logger.error(f"Error indexing document {filename}: {e}", exc_info=True)
            raise

    async def list_documents(self) -> List[DocumentInfo]:
        """List indexed documents."""
        # For now we list documents based on entries in the PGVector table
        # used by PGVectorStore. Each row corresponds to an indexed document
        # with metadata containing filename and doc_id.
        from core.vectorstore.pgvector import PGVectorStore

        documents: List[DocumentInfo] = []
        seen_doc_ids = set()  # Track unique documents by doc_id

        if isinstance(self.vector_store, PGVectorStore):
            try:
                logger.info("Listing documents from vector store...")
                conn = self.vector_store._get_connection()
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT metadata->>'doc_id' AS doc_id, 
                           metadata->>'filename' AS filename, 
                           MIN(created_at) AS created_at
                    FROM rag_documents
                    WHERE metadata->>'doc_id' IS NOT NULL
                    GROUP BY metadata->>'doc_id', metadata->>'filename'
                    ORDER BY created_at DESC
                    """
                )
                rows = cur.fetchall()
                cur.close()
                conn.close()

                logger.info(f"Found {len(rows)} unique documents in vector store")

                for doc_id, filename, created_at in rows:
                    if doc_id and doc_id not in seen_doc_ids:
                        seen_doc_ids.add(doc_id)
                        # created_at is a datetime; convert to ISO string
                        if isinstance(created_at, datetime):
                            ts = created_at.isoformat()
                        else:
                            ts = str(created_at)
                        documents.append(
                            DocumentInfo(
                                id=doc_id,
                                filename=filename or "Unknown",
                                indexed_at=ts,
                            )
                        )
                        logger.debug(f"Added document: {filename} (id: {doc_id})")
            except Exception as e:
                logger.error(f"Error listing documents: {e}", exc_info=True)
        else:
            logger.warning(f"Vector store is not PGVectorStore, cannot list documents")

        logger.info(f"Returning {len(documents)} documents")
        return documents

