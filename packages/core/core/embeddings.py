"""Vector store abstraction for embeddings."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np
from loguru import logger


class EmbeddingsStore(ABC):
    """
    Abstract vector store interface.
    Implement PGVector or Pinecone.
    """

    @abstractmethod
    def add(
        self,
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ):
        """
        Add vectors to the store.

        Args:
            vectors: List of embedding vectors
            metadata: List of metadata dictionaries (one per vector)
            ids: Optional list of IDs (auto-generated if not provided)
        """
        raise NotImplementedError

    @abstractmethod
    def query(
        self,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query similar vectors.

        Args:
            vector: Query vector
            top_k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of results with 'id', 'score', 'metadata' keys
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, ids: List[str]):
        """
        Delete vectors by IDs.

        Args:
            ids: List of vector IDs to delete
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get vectors by IDs.

        Args:
            ids: List of vector IDs

        Returns:
            List of vectors with metadata
        """
        raise NotImplementedError


class EmbeddingGenerator:
    """Generate embeddings using OpenAI."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """
        Initialize embedding generator.

        Args:
            api_key: OpenAI API key
            model: Embedding model name
        """
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    async def agenerate(self, texts: List[str]) -> List[List[float]]:
        """
        Async generate embeddings for texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        try:
            from openai import AsyncOpenAI

            async_client = AsyncOpenAI(api_key=self.client.api_key)
            response = await async_client.embeddings.create(
                model=self.model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Failed to async generate embeddings: {e}")
            raise

