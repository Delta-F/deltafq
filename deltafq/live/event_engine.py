from typing import Any, Callable, Dict, List

EVENT_TICK = "tick"
EVENT_ORDER = "order"
EVENT_TRADE = "trade"
EVENT_ACCOUNT = "account"
EVENT_POSITION = "position"


class EventEngine:
    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable[[Any], None]]] = {}

    def on(self, event_type: str, handler: Callable[[Any], None]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def emit(self, event_type: str, data: Any) -> None:
        for handler in self._handlers.get(event_type, []):
            handler(data)
