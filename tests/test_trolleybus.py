"""Test suite for the trolleybus event bus."""
# pylint: disable=missing-class-docstring,missing-function-docstring,redefined-outer-name
# pylint: disable=unused-argument,use-implicit-booleaness-not-comparison
import threading
from collections.abc import Callable

import pytest

import trolleybus


@pytest.fixture
def bus() -> trolleybus.EventBus:
    return trolleybus.EventBus()


def test_version() -> None:
    assert trolleybus.__version__ == '0.2.0'


class SampleEvent(trolleybus.Event[int, int]):
    name = 'sample-event'


class VoidEvent(trolleybus.Event[int, None]):
    name = 'void-event'


class OptionalResultEvent(trolleybus.Event[int, int | None]):
    name = 'optional-result-event'


class UnnamedEvent(trolleybus.Event[None, None]):
    pass


class TestEvents:
    def test_event_id(self) -> None:
        assert hasattr(SampleEvent, 'event_id')
        assert SampleEvent.event_id != OptionalResultEvent.event_id

    def test_event_name_defaults_to_class_name(self) -> None:
        assert UnnamedEvent.name == 'UnnamedEvent'

    def test_builtin_event_names(self) -> None:
        assert trolleybus.OnStart.name == 'on-start'
        assert trolleybus.OnStarted.name == 'on-started'
        assert trolleybus.OnExit.name == 'on-exit'

    def test_event_not_instantiable(self) -> None:
        with pytest.raises(RuntimeError):
            trolleybus.OnStart()
        with pytest.raises(RuntimeError):
            SampleEvent()


class TestLifecycle:
    def test_on_start(self, bus: trolleybus.EventBus) -> None:
        started: list[bool] = []

        @bus.subscribe(trolleybus.OnStart)
        def _on_start(payload: None) -> None:
            assert payload is None

        @bus.subscribe(trolleybus.OnStarted)
        def _on_started(payload: None) -> None:
            started.append(True)

        results = bus.start()
        assert len(results) == 1
        assert started == [True]

    def test_on_exit(self, bus: trolleybus.EventBus) -> None:
        @bus.subscribe(trolleybus.OnExit)
        def _on_exit(payload: None) -> None:
            assert payload is None

        results = bus.stop()
        assert len(results) == 1
        assert results[0].ok
        assert results[0].value is None
        assert results[0].error is None

    def test_on_exit_suppresses_listener_errors(self, bus: trolleybus.EventBus) -> None:
        @bus.subscribe(trolleybus.OnExit)
        def _on_exit(payload: None) -> None:
            raise RuntimeError('boom')

        results = bus.stop()
        assert len(results) == 1
        assert not results[0].ok
        assert isinstance(results[0].error, RuntimeError)


class TestBroadcast:
    def test_empty_broadcast(self, bus: trolleybus.EventBus) -> None:
        results = bus.broadcast(SampleEvent, 2)
        assert not results

    def test_broadcast_collects_results(self, bus: trolleybus.EventBus) -> None:
        @bus.subscribe(SampleEvent)
        def _on_event(payload: int) -> int:
            return payload * 2

        assert bus.broadcast(SampleEvent, 2) == [4]

    def test_broadcast_stops_on_error(self, bus: trolleybus.EventBus) -> None:
        calls: list[bool] = []

        def _boom(payload: int) -> None:
            raise RuntimeError()

        def _never(payload: int) -> None:
            calls.append(True)

        bus.subscribe(VoidEvent, _boom, priority=60)
        bus.subscribe(VoidEvent, _never, priority=40)

        with pytest.raises(RuntimeError):
            bus.broadcast(VoidEvent, 1)
        assert calls == []


class TestPriority:
    def test_higher_priority_runs_first(self, bus: trolleybus.EventBus) -> None:
        @bus.subscribe(SampleEvent, priority=60)
        def _high_priority(payload: int) -> int:
            return payload * 2

        @bus.subscribe(SampleEvent, priority=40)
        def _low_priority(payload: int) -> int:
            return payload

        results = bus.broadcast(SampleEvent, 2)
        assert results == [4, 2]

    def test_equal_priority_keeps_subscription_order(self, bus: trolleybus.EventBus) -> None:
        calls: list[str] = []

        def _first(payload: int) -> None:
            calls.append('first')

        def _second(payload: int) -> None:
            calls.append('second')

        bus.subscribe(VoidEvent, _first)
        bus.subscribe(VoidEvent, _second)
        bus.broadcast(VoidEvent, 0)
        assert calls == ['first', 'second']

    def test_resubscribe_updates_priority(self, bus: trolleybus.EventBus) -> None:
        calls: list[str] = []

        def _first(payload: int) -> None:
            calls.append('first')

        def _second(payload: int) -> None:
            calls.append('second')

        bus.subscribe(VoidEvent, _first, priority=10)
        bus.subscribe(VoidEvent, _second, priority=50)
        bus.broadcast(VoidEvent, 0)
        assert calls == ['second', 'first']
        calls.clear()

        bus.subscribe(VoidEvent, _first, priority=90)
        bus.broadcast(VoidEvent, 0)
        assert calls == ['first', 'second']


class TestSubscription:
    def test_subscribe_as_decorator_keeps_function(self, bus: trolleybus.EventBus) -> None:
        @bus.subscribe(SampleEvent)
        def _handler(payload: int) -> int:
            return payload * 3

        assert callable(_handler)
        assert _handler(2) == 6

    def test_subscribe_direct_form_returns_callback(self, bus: trolleybus.EventBus) -> None:
        def _handler(payload: int) -> int:
            return payload

        assert bus.subscribe(SampleEvent, _handler) is _handler

    def test_has_listeners_and_clear(self, bus: trolleybus.EventBus) -> None:
        assert not bus.has_listeners(SampleEvent)

        handler = bus.subscribe(SampleEvent, lambda payload: payload)
        assert bus.has_listeners(SampleEvent)

        bus.clear_listeners(SampleEvent)
        assert not bus.has_listeners(SampleEvent)
        assert bus.broadcast(SampleEvent, 1) == []

        bus.unsubscribe(SampleEvent, handler)  # idempotent

    def test_unsubscribe(self, bus: trolleybus.EventBus) -> None:
        def _handler(payload: int) -> int:
            return payload

        bus.subscribe(SampleEvent, _handler)
        bus.unsubscribe(SampleEvent, _handler)
        assert bus.broadcast(SampleEvent, 1) == []

        bus.unsubscribe(SampleEvent, _handler)  # idempotent


class TestBroadcastNothrow:
    def test_collects_values_and_errors(self, bus: trolleybus.EventBus) -> None:
        def _boom(payload: int) -> int:
            raise RuntimeError('boom')

        def _ok(payload: int) -> int:
            return payload * 2

        bus.subscribe(SampleEvent, _boom, priority=60)
        bus.subscribe(SampleEvent, _ok, priority=40)

        results = bus.broadcast_nothrow(SampleEvent, 2)
        assert len(results) == 2

        failed, succeeded = results
        assert not failed.ok
        assert failed.value is None
        assert isinstance(failed.error, RuntimeError)
        assert succeeded.ok
        assert succeeded.value == 4
        assert succeeded.error is None


class TestSendOne:
    def test_empty_send_one(self, bus: trolleybus.EventBus) -> None:
        with pytest.raises(trolleybus.NoListenersError):
            bus.send_one(SampleEvent, 1)

    def test_unknown_event_send_one(self, bus: trolleybus.EventBus) -> None:
        with pytest.raises(trolleybus.NoListenersError):
            bus.send_one(UnnamedEvent, None)

    def test_send_one_uses_highest_priority(self, bus: trolleybus.EventBus) -> None:
        @bus.subscribe(SampleEvent, priority=40)
        def _low_priority(payload: int) -> int:
            raise AssertionError('Should not be called')

        @bus.subscribe(SampleEvent, priority=60)
        def _high_priority(payload: int) -> int:
            return payload * 2

        assert bus.send_one(SampleEvent, 2) == 4


class TestSendAny:
    def test_empty_send_any(self, bus: trolleybus.EventBus) -> None:
        assert bus.send_any(SampleEvent, 1) is None

    def test_send_any_falls_back_to_lower_priority(self, bus: trolleybus.EventBus) -> None:
        @bus.subscribe(OptionalResultEvent, priority=60)
        def _high_priority(payload: int) -> None:
            return None

        @bus.subscribe(OptionalResultEvent, priority=40)
        def _low_priority(payload: int) -> int:
            return payload

        assert bus.send_any(OptionalResultEvent, 2) == 2


class TestSubscriber:
    def test_subscriber(self, bus: trolleybus.EventBus) -> None:
        class MySubscriber(trolleybus.Subscriber):
            @trolleybus.subscribe(SampleEvent)
            def on_event(self, payload: int) -> int:
                return payload * 2

        MySubscriber(bus)
        bus.start()
        assert bus.send_one(SampleEvent, 2) == 4

    def test_subscriber_survives_start_stop_cycles(self, bus: trolleybus.EventBus) -> None:
        class MySubscriber(trolleybus.Subscriber):
            def __init__(self, event_bus: trolleybus.EventBus) -> None:
                super().__init__(event_bus)
                self.calls = 0

            @trolleybus.subscribe(SampleEvent)
            def on_event(self, payload: int) -> int:
                self.calls += 1
                return payload * 2

        subscriber = MySubscriber(bus)
        bus.start()
        assert bus.send_one(SampleEvent, 2) == 4

        bus.stop()
        assert not bus.has_listeners(SampleEvent)

        bus.start()
        assert bus.send_one(SampleEvent, 2) == 4
        assert subscriber.calls == 2

    def test_subscriber_inherited_handlers(self, bus: trolleybus.EventBus) -> None:
        class BaseSubscriber(trolleybus.Subscriber):
            @trolleybus.subscribe(SampleEvent)
            def on_sample(self, payload: int) -> int:
                return payload

        class ChildSubscriber(BaseSubscriber):
            @trolleybus.subscribe(OptionalResultEvent)
            def on_optional(self, payload: int) -> None:
                return None

        ChildSubscriber(bus)
        bus.start()
        assert bus.send_one(SampleEvent, 5) == 5
        assert bus.send_any(OptionalResultEvent, 1) is None


class TestEmitter:
    def test_emitter_mixin(self, bus: trolleybus.EventBus) -> None:
        class MyComponent(trolleybus.Subscriber, trolleybus.EmitterMixin):
            @trolleybus.subscribe(SampleEvent)
            def on_event(self, payload: int) -> int:
                return payload * 2

        component = MyComponent(bus)
        bus.start()
        assert component.send_one(SampleEvent, 2) == 4

    def test_emitter(self, bus: trolleybus.EventBus) -> None:
        emitter = trolleybus.Emitter(bus)
        bus.subscribe(SampleEvent, lambda payload: payload + 1)

        assert emitter.broadcast(SampleEvent, 1) == [2]
        assert emitter.send_one(SampleEvent, 1) == 2
        assert emitter.send_any(SampleEvent, 1) == 2

        results = emitter.broadcast_nothrow(SampleEvent, 1)
        assert results[0].ok
        assert results[0].value == 2


class TestThreadSafety:
    def test_concurrent_subscribe_and_broadcast(self, bus: trolleybus.EventBus) -> None:
        errors: list[Exception] = []

        def _make_listener(offset: int) -> Callable[[int], int]:
            def _listener(payload: int) -> int:
                return payload + offset
            return _listener

        def worker() -> None:
            try:
                for i in range(100):
                    bus.subscribe(SampleEvent, _make_listener(i))
                    bus.broadcast(SampleEvent, i)
            except Exception as error:  # pylint: disable=broad-except
                errors.append(error)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert not errors
