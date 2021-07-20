from typing import ClassVar, Generic, TypeVar
import uuid

TP = TypeVar('TP')
TR = TypeVar('TR')


class EventMeta(type):
    def __new__(cls, name, bases, namespace, **kwds):
        namespace['event_id'] = uuid.uuid4()
        return type.__new__(cls, name, bases, namespace, **kwds)


class Event(Generic[TP, TR], metaclass=EventMeta):
    name: ClassVar[str]
    event_id: ClassVar[uuid.UUID]

    def __init__(self) -> None:
        raise RuntimeError('Event class should not be instanciated')


class OnStart(Event[None, None]):
    name = 'on-start'


class OnStarted(Event[None, None]):
    name = 'on-stop'


class OnExit(Event[None, None]):
    name = 'on-exit'
