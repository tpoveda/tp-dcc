from __future__ import annotations

import time
import uuid
import threading
from typing import TypeVar, Generic
from collections.abc import Callable

from loguru import logger

T = TypeVar("T")


class Event(Generic[T]):
    """Represents an event that can be published and subscribed to."""

    def __init__(self, event_type: str, data: T, source: str = None):
        """Initialize a new event.

        Args:
            event_type: The type of event
                (e.g., "file_created", "asset_imported").
            data: The event data.
            source: The source of the event (e.g., "maya-1", "unreal-2").
        """

        self.id = str(uuid.uuid4())
        self.type = event_type
        self.data = data
        self.source = source
        self.timestamp = time.time()

    def __repr__(self) -> str:
        """Return a string representation of the event.

        Returns:
            A string representation of the event.
        """

        return f"Event(id={self.id}, type={self.type}, source={self.source})"


class EventBus:
    """Central event bus for publishing and subscribing to events."""

    def __init__(self):
        """Initialize the event bus."""

        self._subscribers: dict[str, set[Callable]] = {}
        self._lock = threading.RLock()
        self._history: list[Event] = []
        self._max_history = 100

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers.

        Args:
            event: The event to publish
        """

        with self._lock:
            # Store in history
            self._history.append(event)

            if len(self._history) > self._max_history:
                self._history.pop(0)

            # Get subscribers for this event type.
            subscribers = self._subscribers.get(event.type, set())

            # Also get subscribers for wildcard events.
            wildcard_subscribers = self._subscribers.get("*", set())

            # Combine subscribers.
            all_subscribers = subscribers.union(wildcard_subscribers)

        # Notify subscribers outside the lock to prevent deadlocks.
        for subscriber in all_subscribers:
            try:
                subscriber(event)
            except Exception as e:
                logger.error(f"[tp-rpc][events] Error in event handler: {e}")

    def subscribe(
        self, event_type: str, callback: Callable[[Event], None]
    ) -> Callable[[], None]:
        """Subscribe to events of a specific type.

        Args:
            event_type: The event type to subscribe to, or "*" for all events
            callback: The function to call when an event occurs

        Returns:
            A function that can be called to unsubscribe
        """

        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = set()

            self._subscribers[event_type].add(callback)

        # Return an unsubscribe function.
        def unsubscribe():
            with self._lock:
                if (
                    event_type in self._subscribers
                    and callback in self._subscribers[event_type]
                ):
                    self._subscribers[event_type].remove(callback)
                    if not self._subscribers[event_type]:
                        del self._subscribers[event_type]

        return unsubscribe

    def get_history(
        self, event_type: str | None = None, limit: int = 10
    ) -> list[Event]:
        """Get recent events from history.

        Args:
            event_type: Optional filter for event type
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """

        with self._lock:
            if event_type:
                filtered = [e for e in self._history if e.type == event_type]
                return filtered[-limit:]
            else:
                return self._history[-limit:]


# Global event bus instance
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get the global event bus instance.

    Returns:
        The singleton EventBus instance
    """

    return _event_bus
