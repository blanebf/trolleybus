import inspect
from typing import Any, Callable, Type, Tuple, List

from .bus import EventBus
from . import events


Subscription = List[Tuple[Type[events.Event], Callable[[Any], Any]]]


class Subscriber:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.__subscriptions: Subscription = []

        self.bus.subscribe(events.OnStart, self.on_start)
        self.bus.subscribe(events.OnExit, self.on_exit)

    def on_start(self, _: None):
        for _1, member in inspect.getmembers(self):
            if not hasattr(member, '_subscriber_info'):
                continue
            event, priority = member._subscriber_info
            self.bus.subscribe(event, member, priority)
            self.__subscriptions.append((event, member))

    def on_exit(self, _: None):
        for event, member in self.__subscriptions:
            self.bus.unsubscribe(event, member)


def subscribe(event: Type[events.Event[events.TP, events.TR]], priority: int = 50):
    def _wrapper(callback: Callable[[Type[Subscriber], events.TP], events.TR]):
        callback._subscriber_info = (event, priority)
        return callback
    return _wrapper
