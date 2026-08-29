"""
CRM System - In-Memory Decoupled Event Bus & Dispatcher
"""

import threading
from typing import Callable, Dict, List, Any


EventHandler = Callable[[Dict[str, Any]], None]


class EventBus:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._subscribers = {}
            return cls._instance

    def subscribe(self, event_name: str, handler: EventHandler):
        """Register a subscriber handler for a specific event."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)

    def publish(self, event_name: str, payload: Dict[str, Any], async_dispatch: bool = False):
        """Publish event to all registered subscribers."""
        handlers = self._subscribers.get(event_name, [])
        if not handlers:
            return

        def _dispatch():
            for h in handlers:
                try:
                    h(payload)
                except Exception as ex:
                    print(f"Error handling event '{event_name}': {ex}")

        if async_dispatch:
            thread = threading.Thread(target=_dispatch, daemon=True)
            thread.start()
        else:
            _dispatch()


BUS = EventBus()
