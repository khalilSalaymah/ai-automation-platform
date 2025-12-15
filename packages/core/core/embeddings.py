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
    """Generate embeddings.

    Uses Google Gemini when GEMINI_API_KEY is available; otherwise falls back
    to a simple local hashing-based embedding so development doesn't depend
    on external APIs.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "models/text-embedding-004"):
        """
        Initialize embedding generator.

        Args:
            api_key: Gemini API key (optional, will load from GEMINI_API_KEY env if not provided)
            model: Embedding model name (default: models/text-embedding-004)
        """
        self.use_gemini = False
        self.embedding = None

        # Try to initialize Gemini; if anything is missing, fall back to a
        # local deterministic embedding so uploads still work in dev.
        try:
            import google.generativeai as genai
            from google.generativeai import embedding

            # Load API key from parameter or environment
            if not api_key:
                from .config import get_env
                api_key = get_env("GEMINI_API_KEY")

            if api_key:
                genai.configure(api_key=api_key)
                self.genai = genai
                self.embedding = embedding
                self.model = model
                self.use_gemini = True
            else:
                logger.warning(
                    "GEMINI_API_KEY not found; using local hashing-based "
                    "embeddings for development."
                )
        except ImportError:
            logger.warning(
                "google-generativeai not installed; using local hashing-based "
                "embeddings for development."
            )

    def generate(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        # If Gemini is configured, use it; otherwise fall back to a simple
        # local embedding that hashes text into a fixed-size vector.
        if self.use_gemini and self.embedding is not None:
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
                logger.error(f"Failed to generate embeddings with Gemini: {e}")
                # Fall back to local embeddings instead of crashing

        # Local fallback: simple hashing-based embedding into 768-dim space,
        # which matches the pgvector schema used by PGVectorStore.
        dim = 768
        fallback_embeddings: List[List[float]] = []
        for text in texts:
            vec = np.zeros(dim, dtype=float)
            if text:
                for i, ch in enumerate(text):
                    # Simple, deterministic hash into [0, dim)
                    idx = (ord(ch) + i) % dim
                    vec[idx] += 1.0
                # Normalize to unit length to keep scale reasonable
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec /= norm
            fallback_embeddings.append(vec.tolist())
        return fallback_embeddings

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

