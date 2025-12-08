"""Pinecone implementation."""

from typing import List, Dict, Any, Optional
import pinecone
from loguru import logger

from ..embeddings import EmbeddingsStore
from ..errors import VectorStoreError


class PineconeStore(EmbeddingsStore):
    """Pinecone-based vector store."""

    def __init__(self, api_key: str, index_name: str, environment: Optional[str] = None):
        """
        Initialize Pinecone store.

        Args:
            api_key: Pinecone API key
            index_name: Pinecone index name
            environment: Pinecone environment (deprecated, not needed for serverless)
        """
        self.api_key = api_key
        self.index_name = index_name
        try:
            pinecone.init(api_key=api_key, environment=environment)
            self.index = pinecone.Index(index_name)
            logger.info(f"Connected to Pinecone index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise VectorStoreError(f"Pinecone initialization failed: {e}") from e

    def add(
        self,
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ):
        """Add vectors to the store."""
        import uuid

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in vectors]

        if len(vectors) != len(metadata) or len(vectors) != len(ids):
            raise VectorStoreError("Vectors, metadata, and ids must have same length")

        try:
            # Prepare vectors for Pinecone
            vectors_to_upsert = []
            for vec, meta, vec_id in zip(vectors, metadata, ids):
                vectors_to_upsert.append((vec_id, vec, meta))

            # Upsert in batches
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i : i + batch_size]
                self.index.upsert(vectors=batch)

            logger.info(f"Added {len(vectors)} vectors to Pinecone")
        except Exception as e:
            logger.error(f"Failed to add vectors to Pinecone: {e}")
            raise VectorStoreError(f"Add vectors failed: {e}") from e

    def query(
        self,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query similar vectors."""
        try:
            query_response = self.index.query(
                vector=vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter,
            )

            results = []
            for match in query_response.matches:
                results.append(
                    {
                        "id": match.id,
                        "score": float(match.score),
                        "metadata": match.metadata or {},
                    }
                )

            return results
        except Exception as e:
            logger.error(f"Failed to query Pinecone: {e}")
            raise VectorStoreError(f"Query failed: {e}") from e

    def delete(self, ids: List[str]):
        """Delete vectors by IDs."""
        try:
            self.index.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} vectors from Pinecone")
        except Exception as e:
            logger.error(f"Failed to delete vectors from Pinecone: {e}")
            raise VectorStoreError(f"Delete failed: {e}") from e

    def get(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Get vectors by IDs."""
        try:
            fetch_response = self.index.fetch(ids=ids)
            results = []
            for vec_id, vector_data in fetch_response.vectors.items():
                results.append(
                    {
                        "id": vec_id,
                        "embedding": vector_data.values,
                        "metadata": vector_data.metadata or {},
                    }
                )
            return results
        except Exception as e:
            logger.error(f"Failed to get vectors from Pinecone: {e}")
            raise VectorStoreError(f"Get vectors failed: {e}") from e

