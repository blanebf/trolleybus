"""Event marker classes.

Events are never instantiated: an event class only carries the payload type
``TP``, the listener result type ``TR``, a unique ``event_id`` and a
human-readable ``name``.
"""
from typing import Any, ClassVar, Generic, TypeVar
import uuid

TP = TypeVar('TP')
TR = TypeVar('TR')


class EventMeta(type):
    """Metaclass that assigns a unique identifier and a default name to every event class."""

    def __new__(
            mcs,
            name: str,
            bases: tuple[type, ...],
            namespace: dict[str, Any],
            **kwds: Any
    ) -> 'EventMeta':
        namespace.setdefault('event_id', uuid.uuid4())
        namespace.setdefault('name', name)
        return type.__new__(mcs, name, bases, namespace, **kwds)


class Event(Generic[TP, TR], metaclass=EventMeta):
    """Base class for all events.

    :cvar name: human-readable event name. Defaults to the class name if not
        defined explicitly.
    :cvar event_id: unique identifier of the event class
    """
    name: ClassVar[str]
    event_id: ClassVar[uuid.UUID]

    def __init__(self) -> None:
        raise RuntimeError(f'{type(self).__name__} should not be instantiated')


class OnStart(Event[None, None]):
    """Emitted by :meth:`~trolleybus.EventBus.start` before the bus is considered started."""
    name = 'on-start'


class OnStarted(Event[None, None]):
    """Emitted by :meth:`~trolleybus.EventBus.start` once all ``OnStart`` listeners returned."""
    name = 'on-started'


class OnExit(Event[None, None]):
    """Emitted by :meth:`~trolleybus.EventBus.stop`."""
    name = 'on-exit'
