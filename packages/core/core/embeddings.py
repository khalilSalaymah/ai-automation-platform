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
    """Generate embeddings using Google Gemini."""

    def __init__(self, api_key: Optional[str] = None, model: str = "models/text-embedding-004"):
        """
        Initialize embedding generator.

        Args:
            api_key: Gemini API key (optional, will load from GEMINI_API_KEY env if not provided)
            model: Embedding model name (default: models/text-embedding-004)
        """
        try:
            import google.generativeai as genai
            from google.generativeai import embedding
        except ImportError:
            raise ImportError(
                "Google Generative AI SDK not installed. "
                "Install with: pip install google-generativeai"
            )

        # Load API key from parameter or environment
        if not api_key:
            from .config import get_env
            api_key = get_env("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found. Provide api_key parameter or set GEMINI_API_KEY environment variable.")

        genai.configure(api_key=api_key)
        self.genai = genai
        self.embedding = embedding
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
            embeddings = []
            for text in texts:
                response = self.embedding.embed_content(
                    model=self.model,
                    content=text
                )
                embeddings.append(response["embedding"])
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    async def agenerate(self, texts: List[str]) -> List[List[float]]:
        """
        Async generate embeddings for texts.
        
        Note: Google Generative AI SDK doesn't have native async support,
        so this runs synchronously in an executor.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        try:
            import asyncio
            
            # Run synchronous generate in executor
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(None, self.generate, texts)
            return embeddings
        except Exception as e:
            logger.error(f"Failed to async generate embeddings: {e}")
            raise

