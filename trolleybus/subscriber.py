"""Declarative, lifecycle-aware subscriptions built around :class:`~trolleybus.EventBus`."""
from collections.abc import Callable, Iterator
from typing import Any

from . import events
from .bus import DEFAULT_PRIORITY, EventBus

SubscriberInfo = tuple[type[events.Event[Any, Any]], int]


class Subscriber:
    """Base class for components that attach their methods to the event bus.

    Methods decorated with :func:`subscribe` are registered with the bus when
    the bus starts (:class:`~trolleybus.OnStart`) and detached again when the
    bus exits (:class:`~trolleybus.OnExit`), so a subscriber survives any
    number of start/stop cycles.

    The subscriber itself stays attached to the bus for the whole lifetime of
    the bus; create a new :class:`EventBus` (or clear its listeners) to get
    rid of it.
    """

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self._subscriptions: list[tuple[type[events.Event[Any, Any]], Callable[[Any], Any]]] = []

        self.bus.subscribe(events.OnStart, self.on_start)
        self.bus.subscribe(events.OnExit, self.on_exit)

    def on_start(self, _: None) -> None:
        """Registers all decorated member methods with the bus."""
        for member_name, (event, priority) in self._subscriber_methods():
            member = getattr(self, member_name)
            self.bus.subscribe(event, member, priority)
            if (event, member) not in self._subscriptions:
                self._subscriptions.append((event, member))

    def on_exit(self, _: None) -> None:
        """Detaches all decorated member methods from the bus."""
        for event, member in self._subscriptions:
            self.bus.unsubscribe(event, member)
        self._subscriptions.clear()

    def _subscriber_methods(self) -> Iterator[tuple[str, SubscriberInfo]]:
        """Yields ``(member name, (event, priority))`` for all decorated members.

        Walks the MRO instead of evaluating instance attributes, so decorated
        methods can be inherited and side-effectful attributes (e.g.
        properties) are never touched. Overridden members are reported only
        once, using the nearest definition.
        """
        seen: set[str] = set()
        for klass in type(self).__mro__:
            for member_name, attribute in vars(klass).items():
                if member_name in seen:
                    continue
                seen.add(member_name)
                info = getattr(attribute, '_subscriber_info', None)
                if info is not None:
                    yield member_name, info


def subscribe(
        event: type[events.Event[events.TP, events.TR]],
        priority: int = DEFAULT_PRIORITY
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Marks a :class:`Subscriber` method as a handler for the event.

    :param event: type of the event
    :param priority: subscriber priority, higher runs first, defaults to
        `~trolleybus.DEFAULT_PRIORITY`
    """
    def _wrapper(callback: Callable[..., Any]) -> Callable[..., Any]:
        setattr(callback, '_subscriber_info', (event, priority))
        return callback
    return _wrapper
