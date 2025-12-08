"""Redis-based session memory for agent conversations."""

import json
import redis
from typing import Any, Dict, List, Optional
from datetime import timedelta
from loguru import logger

from .errors import MemoryError


class RedisSessionMemory:
    """Redis-based session memory store."""

    def __init__(self, url: str, default_ttl: int = 3600):
        """
        Initialize Redis session memory.

        Args:
            url: Redis connection URL
            default_ttl: Default TTL in seconds (default: 1 hour)
        """
        try:
            self.r = redis.Redis.from_url(url, decode_responses=True)
            self.default_ttl = default_ttl
            # Test connection
            self.r.ping()
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise MemoryError(f"Redis connection failed: {e}") from e

    def save(self, session_id: str, data: Dict[str, Any], ttl: Optional[int] = None):
        """
        Save session data.

        Args:
            session_id: Unique session identifier
            data: Data dictionary to save
            ttl: Time to live in seconds (uses default if not provided)
        """
        try:
            key = f"session:{session_id}"
            # Serialize complex values
            serialized = {}
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    serialized[k] = json.dumps(v)
                else:
                    serialized[k] = str(v)

            self.r.hset(key, mapping=serialized)
            ttl = ttl or self.default_ttl
            self.r.expire(key, ttl)
            logger.debug(f"Saved session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            raise MemoryError(f"Failed to save session: {e}") from e

    def load(self, session_id: str) -> Dict[str, Any]:
        """
        Load session data.

        Args:
            session_id: Unique session identifier

        Returns:
            Session data dictionary
        """
        try:
            key = f"session:{session_id}"
            data = self.r.hgetall(key)
            if not data:
                return {}

            # Deserialize JSON values
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = v

            return result
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            raise MemoryError(f"Failed to load session: {e}") from e

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Append a message to session conversation history.

        Args:
            session_id: Unique session identifier
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Optional metadata dictionary
        """
        try:
            key = f"session:{session_id}"
            messages_key = f"{key}:messages"

            message = {
                "role": role,
                "content": content,
                "metadata": metadata or {},
            }

            self.r.rpush(messages_key, json.dumps(message))
            self.r.expire(messages_key, self.default_ttl)
            logger.debug(f"Appended message to session {session_id}")
        except Exception as e:
            logger.error(f"Failed to append message: {e}")
            raise MemoryError(f"Failed to append message: {e}") from e

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            List of message dictionaries
        """
        try:
            key = f"session:{session_id}"
            messages_key = f"{key}:messages"
            messages = self.r.lrange(messages_key, 0, -1)

            result = []
            for msg_json in messages:
                try:
                    result.append(json.loads(msg_json))
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse message: {msg_json}")

            return result
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            raise MemoryError(f"Failed to get messages: {e}") from e

    def clear(self, session_id: str):
        """
        Clear all data for a session.

        Args:
            session_id: Unique session identifier
        """
        try:
            key = f"session:{session_id}"
            self.r.delete(key)
            self.r.delete(f"{key}:messages")
            logger.debug(f"Cleared session {session_id}")
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            raise MemoryError(f"Failed to clear session: {e}") from e

    def exists(self, session_id: str) -> bool:
        """
        Check if session exists.

        Args:
            session_id: Unique session identifier

        Returns:
            True if session exists, False otherwise
        """
        try:
            key = f"session:{session_id}"
            return self.r.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check session existence: {e}")
            return False

