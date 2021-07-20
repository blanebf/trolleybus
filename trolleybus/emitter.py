from typing import Optional, Tuple, Type, List, Union
from .bus import EventBus
from . import events


class EmitterMixin:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def broadcast(
            self,
            event: Type[events.Event[events.TP, events.TR]],
            payload: events.TP
        ) -> List[events.TR]:
        return self.bus.broadcast(event, payload)

    def broadcast_nothrow(
            self,
            event: Type[events.Event[events.TP, events.TR]],
            payload: events.TP
        ) -> List[Tuple[Union[events.TR, Exception], bool]]:
        return self.bus.broadcast_nothrow(event, payload)

    def send_one(
            self,
            event: Type[events.Event[events.TP, events.TR]],
            payload: events.TP
        ) -> events.TR:
        return self.bus.send_one(event, payload)

    def send_any(
            self,
            event: Type[events.Event[events.TP, events.TR]],
            payload: events.TP
        ) -> Optional[events.TR]:
        return self.bus.send_any(event, payload)
