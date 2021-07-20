# -*- coding: utf-8 -*-
"""
Evemt bus module.

Provides simple implementation of publish/subscibire model.

`EventBus` class provides all essential methods for publishing events and
subscribing to them.

"""
import operator
import logging
import uuid

from typing import Any, Callable, Dict, List, Set, Tuple, Type, Union, Optional

from . import events


ListenerMap = Dict[uuid.UUID, Set[Callable[[Any], Any]]]
PriorityMap = Dict[Tuple[uuid.UUID, Callable[[Any], Any]], int]


class NoListenersError(Exception):
    """Raised when there are no listeners for requested event.

    This error is not raised when using broadcast method."""


class EventBus:
    """Event bus for implementing simple publish/subscribe model.

    Class provides essential method for subscribing to events and broadcasting
    them. All handling is done synchronously according to subscriber's priority.

    :ivar listeners: mapping event -> listeners
    :ivar log: event bus logger
    """
    default_events: List[Type[events.Event]] = [
        events.OnStart,
        events.OnStarted,
        events.OnExit
    ]

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    def __init__(self):
        """Event bus initialization"""

        self.listeners: ListenerMap = {
            event.event_id: set()
            for event in self.default_events
        }
        self._priorities: PriorityMap = {}
        self.log = logging.getLogger(self.name())

    def start(self):
        self.log.info('Event bus is starting...')
        return self.broadcast(events.OnStart, None)

    def stop(self):
        self.log.info('Event bus is exiting...')
        return self.broadcast_nothrow(events.OnExit, None)

    def subscribe(
            self,
            event: Type[events.Event[events.TP, events.TR]],
            callback: Callable[[events.TP], events.TR] = None,
            priority: int = 50
        ) -> Callable[[Callable[[events.TP], events.TR]], None]:
        """Subscribes a listener to the event

        :param event:
        :param callback: callback that will be called when the event is fired
        :param priority: subscriber priority, defaults to 50
        """
        def decorator(_callback: Callable[[events.TP], events.TR]):
            self.subscribe(event, _callback, priority)
        if callback is not None:
            callbacks = self.listeners.setdefault(event.event_id, set())
            callbacks.add(callback)
            self._priorities[(event.event_id, callback)] = priority
        return decorator

    def unsubscribe(
            self,
            event: Type[events.Event[events.TP, events.TR]],
            callback: Callable[[events.TP], events.TR]
        ):
        """Unsubscribes a listener from event

        :param event:
        :param callback: subscriber
        """
        listeners = self.listeners.get(event.event_id)
        if listeners and callback in listeners:
            listeners.discard(callback)
            del self._priorities[(event.event_id, callback)]

    def broadcast(
            self,
            event: Type[events.Event[events.TP, events.TR]],
            payload: events.TP
        ) -> List[events.TR]:
        """Broadcast the event to all listeners on the channel.

        Event is handled according to listeners priority.

        :param event:
        :return: list of results from all listeners
        """
        results = []  # type: List[events.TR]
        if event.event_id not in self.listeners:
            return results

        for _, listener in self._sort_listeners(event.event_id):
            try:
                result = listener(payload)  # type: events.TR
            except Exception as error:
                self.log.exception('Handler failure %r [args: %r]: %r', listener, payload, error)
                raise
            results.append(result)
        return results

    def broadcast_nothrow(
            self,
            event: Type[events.Event[events.TP, events.TR]],
            payload: events.TP
        ) -> List[Tuple[Union[events.TR, Exception], bool]]:
        """Broadcast the event to all listeners on the channel.

        Event is handled according to listeners priority. In case one of the
        listeners would rise an exception, it won't be raised, but instead it
        would be appended to results

        :param event:
        :return: list of tuples. Each tuple would contain result from the
                 listener or exception, if it occured. Second value of the tuple
                 would be either `True` (if no exception occured) or `False` (
                 if exception did occur)
        """
        results = []  # type: List[Tuple[Union[events.TR, Exception], bool]]
        if event.event_id not in self.listeners:
            return results

        for _, listener in self._sort_listeners(event.event_id):
            try:
                result = listener(payload)  # type: events.TR
            except Exception as error:  # pylint: disable=broad-except
                results.append((error, True))
            else:
                results.append((result, False))
        return results

    def send_one(
            self,
            event: Type[events.Event[events.TP, events.TR]],
            payload: events.TP
        ) -> events.TR:
        """Sends event to one listiner with highest priority

        :param event:
        :raises NoListenersError: raised when no listener found for specified event
        :return: result from a listiner with highest priority
        """
        try:
            listener = self._sort_listeners(event.event_id)[0][1]
        except (IndexError, KeyError):
            msg = f'No listeners for {event.name}'
            self.log.error(msg)
            raise NoListenersError(msg)
        return listener(payload)

    def send_any(
            self,
            event: Type[events.Event[events.TP, events.TR]],
            payload: events.TP
        ) -> Optional[events.TR]:
        """Broadcast the specfied event and returns firts none `None` result

        If all listeners return `None` or no listeners present for specfied event
        method returns `None`

        :param event:
        :return: first none `None` result or `None`
        """
        if event.event_id not in self.listeners:
            return None
        for _, listener in self._sort_listeners(event.event_id):
            try:
                result = listener(payload)  # type: Optional[events.TR]
            except Exception as error:
                self.log.exception('Handler failure %r [args: %r]: %r', listener, payload, error)
                raise
            if result is not None:
                return result
        return None

    def _sort_listeners(self, event_name):
        unsorted = (
            (self._priorities[(event_name, l)], l)
            for l in self.listeners[event_name]
        )
        return sorted(unsorted, key=operator.itemgetter(0))
