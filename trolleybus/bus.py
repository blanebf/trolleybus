"""Event bus module.

Provides a simple implementation of the publish/subscribe model.

:class:`~trolleybus.EventBus` provides all essential methods for publishing
events and subscribing to them.
"""
import logging
import threading
import uuid

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, overload

from . import events
from .events import TP, TR

Listener = Callable[[Any], Any]
ListenerMap = dict[uuid.UUID, list[Listener]]
PriorityMap = dict[tuple[uuid.UUID, Listener], int]

DEFAULT_PRIORITY = 50


@dataclass(frozen=True)
class ListenerResult(Generic[TR]):
    """Outcome of a single listener as returned by :meth:`EventBus.broadcast_nothrow`.

    :ivar value: value returned by the listener, `None` if it raised
    :ivar error: exception raised by the listener, `None` if it returned normally
    """
    value: TR | None
    error: Exception | None

    @property
    def ok(self) -> bool:
        """`True` when the listener finished without raising an exception."""
        return self.error is None


class NoListenersError(Exception):
    """Raised when there are no listeners for the requested event.

    This error is not raised by the :meth:`~trolleybus.EventBus.broadcast`,
    :meth:`~trolleybus.EventBus.broadcast_nothrow` or
    :meth:`~trolleybus.EventBus.send_any` methods.
    """


class EventBus:
    """Event bus implementing a simple publish/subscribe model.

    All event handling is synchronous: listeners run in the calling thread,
    in descending priority order (higher priority value runs first).
    Listeners with equal priority run in subscription order.

    The bus is safe to use from multiple threads: subscription management is
    protected by a reentrant lock and listeners are invoked outside of that
    lock, so listeners may broadcast events or (un)subscribe to them without
    risking a deadlock.

    :ivar listeners: mapping event id -> listeners, in subscription order
    :ivar log: event bus logger
    """
    default_events: list[type[events.Event[Any, Any]]] = [
        events.OnStart,
        events.OnStarted,
        events.OnExit
    ]

    @classmethod
    def name(cls) -> str:
        """Name of the bus, used as the base name of its logger."""
        return cls.__name__

    def __init__(self) -> None:
        self.listeners: ListenerMap = {
            event.event_id: []
            for event in self.default_events
        }
        self._priorities: PriorityMap = {}
        self._lock = threading.RLock()
        self.log = logging.getLogger(self.name())

    def start(self) -> list[None]:
        """Sends the :class:`~trolleybus.OnStart` event.

        Once all ``OnStart`` listeners have returned, the
        :class:`~trolleybus.OnStarted` event is sent.

        :return: results of the ``OnStart`` listeners
        """
        self.log.info('Event bus is starting...')
        results = self.broadcast(events.OnStart, None)
        self.broadcast(events.OnStarted, None)
        return results

    def stop(self) -> list[ListenerResult[None]]:
        """Sends the :class:`~trolleybus.OnExit` event.

        Exceptions raised by ``OnExit`` listeners are suppressed and returned
        as :class:`ListenerResult` items so that every listener gets a chance
        to shut down.

        :return: per-listener results of the ``OnExit`` listeners
        """
        self.log.info('Event bus is exiting...')
        return self.broadcast_nothrow(events.OnExit, None)

    @overload
    def subscribe(
            self,
            event: type[events.Event[TP, TR]],
            callback: Callable[[TP], TR],
            priority: int = DEFAULT_PRIORITY
    ) -> Callable[[TP], TR]: ...

    @overload
    def subscribe(
            self,
            event: type[events.Event[TP, TR]],
            callback: None = None,
            priority: int = DEFAULT_PRIORITY
    ) -> Callable[[Callable[[TP], TR]], Callable[[TP], TR]]: ...

    def subscribe(
            self,
            event: type[events.Event[TP, TR]],
            callback: Callable[[TP], TR] | None = None,
            priority: int = DEFAULT_PRIORITY
    ) -> Callable[[TP], TR] | Callable[[Callable[[TP], TR]], Callable[[TP], TR]]:
        """Subscribes the listener to the event.

        Can be called directly or used as a decorator::

            bus.subscribe(MyEvent, handler)

            @bus.subscribe(MyEvent, priority=60)
            def handler(payload): ...

        Subscribing an already registered listener only updates its priority.

        :param event: type of the event
        :param callback: callback that will be called when the event is fired.
            When omitted, a decorator is returned instead.
        :param priority: subscriber priority, higher runs first, defaults to
            `~trolleybus.DEFAULT_PRIORITY`
        :return: the callback itself (direct form) or a decorator that
            registers and returns the decorated function
        """
        def decorator(_callback: Callable[[TP], TR]) -> Callable[[TP], TR]:
            self.subscribe(event, _callback, priority)
            return _callback

        if callback is None:
            return decorator

        with self._lock:
            callbacks = self.listeners.setdefault(event.event_id, [])
            if callback not in callbacks:
                callbacks.append(callback)
            self._priorities[(event.event_id, callback)] = priority
        return callback

    def unsubscribe(
            self,
            event: type[events.Event[TP, TR]],
            callback: Callable[[TP], TR]
    ) -> None:
        """Unsubscribes the listener from the event.

        Unsubscribing a listener that is not registered is a silent no-op.

        :param event: type of the event
        :param callback: callback that is to be removed from event listeners
        """
        with self._lock:
            callbacks = self.listeners.get(event.event_id)
            if not callbacks:
                return
            try:
                callbacks.remove(callback)
            except ValueError:
                return
            self._priorities.pop((event.event_id, callback), None)

    def has_listeners(self, event: type[events.Event[Any, Any]]) -> bool:
        """Returns `True` if at least one listener is subscribed to the event."""
        with self._lock:
            return bool(self.listeners.get(event.event_id))

    def clear_listeners(self, event: type[events.Event[Any, Any]]) -> None:
        """Removes all listeners subscribed to the event."""
        with self._lock:
            callbacks = self.listeners.get(event.event_id)
            if not callbacks:
                return
            for callback in callbacks:
                self._priorities.pop((event.event_id, callback), None)
            callbacks.clear()

    def broadcast(
            self,
            event: type[events.Event[TP, TR]],
            payload: TP
    ) -> list[TR]:
        """Broadcasts the event to all listeners.

        Listeners are called in descending priority order. If a listener
        raises an exception it is logged, re-raised and the remaining
        listeners are not called.

        :param event: type of the event
        :param payload: value passed to every listener
        :return: results from all listeners, in call order
        """
        with self._lock:
            listeners = self._sorted_listeners(event.event_id)

        results: list[TR] = []
        for listener in listeners:
            try:
                result: TR = listener(payload)
            except Exception as error:
                self.log.exception('Handler failure %r [payload: %r]: %r', listener, payload, error)
                raise
            results.append(result)
        return results

    def broadcast_nothrow(
            self,
            event: type[events.Event[TP, TR]],
            payload: TP
    ) -> list[ListenerResult[TR]]:
        """Broadcasts the event to all listeners, suppressing listener exceptions.

        Listeners are called in descending priority order. If a listener
        raises an exception it is logged and captured in the corresponding
        :class:`ListenerResult`, the remaining listeners are still called.

        :param event: type of the event
        :param payload: value passed to every listener
        :return: one :class:`ListenerResult` per listener, in call order
        """
        with self._lock:
            listeners = self._sorted_listeners(event.event_id)

        results: list[ListenerResult[TR]] = []
        for listener in listeners:
            try:
                value: TR = listener(payload)
            except Exception as error:  # pylint: disable=broad-except
                self.log.exception('Handler failure %r [payload: %r]: %r', listener, payload, error)
                results.append(ListenerResult(None, error))
            else:
                results.append(ListenerResult(value, None))
        return results

    def send_one(
            self,
            event: type[events.Event[TP, TR]],
            payload: TP
    ) -> TR:
        """Sends the event to the single listener with the highest priority.

        :param event: type of the event
        :param payload: value passed to the listener
        :raises NoListenersError: raised when no listener is subscribed to the event
        :return: result from the listener with the highest priority
        """
        with self._lock:
            listeners = self._sorted_listeners(event.event_id)
            listener = listeners[0] if listeners else None

        if listener is None:
            msg = f'No listeners for {event.name}'
            self.log.error(msg)
            raise NoListenersError(msg)

        result: TR = listener(payload)
        return result

    def send_any(
            self,
            event: type[events.Event[TP, TR]],
            payload: TP
    ) -> TR | None:
        """Broadcasts the event and returns the first non-`None` result.

        Listeners are called in descending priority order until one of them
        returns a value other than `None`. If all listeners return `None` or
        no listeners are registered for the event, `None` is returned.

        :param event: type of the event
        :param payload: value passed to every listener
        :return: first non-`None` result or `None`
        """
        with self._lock:
            listeners = self._sorted_listeners(event.event_id)

        for listener in listeners:
            try:
                result: TR | None = listener(payload)
            except Exception as error:
                self.log.exception('Handler failure %r [payload: %r]: %r', listener, payload, error)
                raise
            if result is not None:
                return result
        return None

    def _sorted_listeners(self, event_id: uuid.UUID) -> list[Listener]:
        """Returns listeners of the event ordered by descending priority.

        Stable for equal priorities: subscription order is preserved.
        Must be called with `self._lock` held.
        """
        listeners = self.listeners.get(event_id, [])
        return sorted(listeners, key=lambda listener: -self._priorities[(event_id, listener)])
