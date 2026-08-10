"""Convenience facade for emitting events."""
from . import events
from .bus import EventBus, ListenerResult


class EmitterMixin:
    """Mixin exposing the :class:`~trolleybus.EventBus` emission shortcuts.

    The host class must provide a ``bus`` attribute. Either call
    ``EmitterMixin.__init__`` (standalone usage) or rely on another base
    class such as :class:`~trolleybus.Subscriber` to set it up.
    """

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def broadcast(
            self,
            event: type[events.Event[events.TP, events.TR]],
            payload: events.TP
    ) -> list[events.TR]:
        """See :meth:`~trolleybus.EventBus.broadcast`."""
        return self.bus.broadcast(event, payload)

    def broadcast_nothrow(
            self,
            event: type[events.Event[events.TP, events.TR]],
            payload: events.TP
    ) -> list[ListenerResult[events.TR]]:
        """See :meth:`~trolleybus.EventBus.broadcast_nothrow`."""
        return self.bus.broadcast_nothrow(event, payload)

    def send_one(
            self,
            event: type[events.Event[events.TP, events.TR]],
            payload: events.TP
    ) -> events.TR:
        """See :meth:`~trolleybus.EventBus.send_one`."""
        return self.bus.send_one(event, payload)

    def send_any(
            self,
            event: type[events.Event[events.TP, events.TR]],
            payload: events.TP
    ) -> events.TR | None:
        """See :meth:`~trolleybus.EventBus.send_any`."""
        return self.bus.send_any(event, payload)


class Emitter(EmitterMixin):
    """Standalone emitter bound to an event bus."""
