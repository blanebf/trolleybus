"""Small publish/subscribe event bus with typed events."""
from .bus import DEFAULT_PRIORITY, EventBus, ListenerResult, NoListenersError
from .emitter import Emitter, EmitterMixin
from .events import Event, OnExit, OnStart, OnStarted
from .subscriber import Subscriber, subscribe

__version__ = '0.2.0'

__all__ = [
    'DEFAULT_PRIORITY',
    'Emitter',
    'EmitterMixin',
    'Event',
    'EventBus',
    'ListenerResult',
    'NoListenersError',
    'OnExit',
    'OnStart',
    'OnStarted',
    'Subscriber',
    '__version__',
    'subscribe',
]
