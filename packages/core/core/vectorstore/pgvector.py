"""PGVector implementation."""

from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import execute_values
import pgvector
from pgvector.psycopg2 import register_vector
from loguru import logger

from ..embeddings import EmbeddingsStore
from ..errors import VectorStoreError


class PGVectorStore(EmbeddingsStore):
    """PGVector-based vector store."""

    def __init__(self, uri: str, table_name: str = "embeddings"):
        """
        Initialize PGVector store.

        Args:
            uri: PostgreSQL connection URI
            table_name: Table name for storing vectors
        """
        self.uri = uri
        self.table_name = table_name
        self._ensure_table()

    def _get_connection(self):
        """Get database connection."""
        try:
            conn = psycopg2.connect(self.uri)
            register_vector(conn)
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise VectorStoreError(f"Connection failed: {e}") from e

    def _ensure_table(self):
        """Create table if it doesn't exist."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Enable pgvector extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Create table
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    vector_id VARCHAR(255) UNIQUE NOT NULL,
                    embedding vector(1536),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Create index for similarity search
            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx
                ON {self.table_name}
                USING ivfflat (embedding vector_cosine_ops)
                """
            )

            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Ensured table {self.table_name} exists")
        except Exception as e:
            logger.error(f"Failed to ensure table: {e}")
            raise VectorStoreError(f"Table creation failed: {e}") from e

    def add(
        self,
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ):
        """Add vectors to the store."""
        import uuid
        import json

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in vectors]

        if len(vectors) != len(metadata) or len(vectors) != len(ids):
            raise VectorStoreError("Vectors, metadata, and ids must have same length")

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            data = []
            for vec, meta, vec_id in zip(vectors, metadata, ids):
                data.append((vec_id, vec, json.dumps(meta)))

            execute_values(
                cur,
                f"""
                INSERT INTO {self.table_name} (vector_id, embedding, metadata)
                VALUES %s
                ON CONFLICT (vector_id) DO UPDATE
                SET embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata
                """,
                data,
            )

            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Added {len(vectors)} vectors to {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to add vectors: {e}")
            raise VectorStoreError(f"Add vectors failed: {e}") from e

    def query(
        self,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query similar vectors."""
        import json

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Build query
            query = f"""
                SELECT vector_id, embedding, metadata,
                       1 - (embedding <=> %s::vector) as similarity
                FROM {self.table_name}
            """

            params = [vector]

            if filter:
                # Add metadata filter (simple JSONB filter)
                conditions = []
                for key, value in filter.items():
                    conditions.append(f"metadata->>'{key}' = %s")
                    params.append(str(value))
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY embedding <=> %s::vector LIMIT %s"
            params.extend([vector, top_k])

            cur.execute(query, params)
            results = cur.fetchall()

            cur.close()
            conn.close()

            return [
                {
                    "id": row[0],
                    "score": float(row[3]),
                    "metadata": json.loads(row[2]) if isinstance(row[2], str) else row[2],
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Failed to query vectors: {e}")
            raise VectorStoreError(f"Query failed: {e}") from e

    def delete(self, ids: List[str]):
        """Delete vectors by IDs."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            placeholders = ",".join(["%s"] * len(ids))
            cur.execute(
                f"DELETE FROM {self.table_name} WHERE vector_id IN ({placeholders})",
                ids,
            )

            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Deleted {len(ids)} vectors")
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            raise VectorStoreError(f"Delete failed: {e}") from e

    def get(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Get vectors by IDs."""
        import json

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            placeholders = ",".join(["%s"] * len(ids))
            cur.execute(
                f"""
                SELECT vector_id, embedding, metadata
                FROM {self.table_name}
                WHERE vector_id IN ({placeholders})
                """,
                ids,
            )

            results = cur.fetchall()
            cur.close()
            conn.close()

            return [
                {
                    "id": row[0],
                    "embedding": row[1],
                    "metadata": json.loads(row[2]) if isinstance(row[2], str) else row[2],
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Failed to get vectors: {e}")
            raise VectorStoreError(f"Get vectors failed: {e}") from e

