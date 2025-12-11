"""Event bus for inter-app communication using Redis pub/sub."""

import json
from typing import Callable, Optional, Dict, Any
from datetime import datetime
import redis
from .logger import logger
from .config import get_settings
from .scheduler_models import EventMessage

settings = get_settings()


class EventBus:
    """Redis-based event bus for inter-app communication."""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize event bus.

        Args:
            redis_url: Redis connection URL. Defaults to settings.redis_url
        """
        self.redis_url = redis_url or settings.redis_url
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self._subscribers: Dict[str, list] = {}

    def publish(
        self,
        event_type: str,
        source_agent: str,
        payload: Dict[str, Any],
        target_agent: Optional[str] = None,
    ) -> None:
        """
        Publish an event.

        Args:
            event_type: Type of event (e.g., "task.completed", "email.received")
            source_agent: Name of the agent publishing the event
            payload: Event data
            target_agent: Specific agent to target, or None for broadcast
        """
        channel = f"events:{target_agent}" if target_agent else "events:broadcast"
        event = EventMessage(
            event_type=event_type,
            source_agent=source_agent,
            target_agent=target_agent,
            payload=payload,
            timestamp=datetime.utcnow(),
        )
        message = event.model_dump_json()
        try:
            self.redis_client.publish(channel, message)
            logger.info(f"Published event {event_type} from {source_agent} to {channel}")
        except Exception as e:
            logger.error(f"Error publishing event: {e}")

    def subscribe(
        self,
        agent_name: str,
        event_type: Optional[str] = None,
        callback: Optional[Callable[[EventMessage], None]] = None,
    ) -> None:
        """
        Subscribe to events.

        Args:
            agent_name: Name of the agent subscribing
            event_type: Specific event type to subscribe to, or None for all
            callback: Callback function to handle events
        """
        channels = [
            f"events:{agent_name}",  # Direct messages
            "events:broadcast",  # Broadcast messages
        ]
        for channel in channels:
            self.pubsub.subscribe(channel)
            if channel not in self._subscribers:
                self._subscribers[channel] = []
            if callback:
                self._subscribers[channel].append((event_type, callback))
        logger.info(f"Subscribed {agent_name} to channels: {channels}")

    def listen(self, timeout: Optional[float] = None) -> Optional[EventMessage]:
        """
        Listen for events (blocking).

        Args:
            timeout: Timeout in seconds, or None for blocking

        Returns:
            EventMessage if received, None on timeout
        """
        try:
            message = self.pubsub.get_message(timeout=timeout)
            if message and message["type"] == "message":
                data = json.loads(message["data"])
                event = EventMessage(**data)
                channel = message["channel"]

                # Call registered callbacks
                if channel in self._subscribers:
                    for event_type_filter, callback in self._subscribers[channel]:
                        if event_type_filter is None or event_type_filter == event.event_type:
                            try:
                                callback(event)
                            except Exception as e:
                                logger.error(f"Error in event callback: {e}")

                return event
        except Exception as e:
            logger.error(f"Error listening for events: {e}")
        return None

    def unsubscribe(self, agent_name: str) -> None:
        """
        Unsubscribe from events.

        Args:
            agent_name: Name of the agent unsubscribing
        """
        channels = [f"events:{agent_name}", "events:broadcast"]
        for channel in channels:
            self.pubsub.unsubscribe(channel)
            if channel in self._subscribers:
                del self._subscribers[channel]
        logger.info(f"Unsubscribed {agent_name} from events")

    def close(self) -> None:
        """Close event bus connections."""
        self.pubsub.close()
        self.redis_client.close()

