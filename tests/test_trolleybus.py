from trolleybus import subscriber
from typing import Optional

import pytest

import trolleybus


@pytest.fixture
def bus():
    return trolleybus.EventBus()


def test_version():
    assert trolleybus.__version__ == '0.1.0'


class TestEvent(trolleybus.Event[int, int]):
    name = 'test-event'


class TestEventOptional(trolleybus.Event[int, Optional[int]]):
    name = 'test-event-optional'


def test_event_id():
    assert hasattr(TestEvent, 'event_id')
    assert TestEvent.event_id != TestEventOptional.event_id


def test_on_start(bus: trolleybus.EventBus):
    @bus.subscribe(trolleybus.OnStart)
    def _on_start(payload: None):
        assert True
    results = bus.start()
    assert len(results) == 1


def test_on_exit(bus: trolleybus.EventBus):
    @bus.subscribe(trolleybus.OnExit)
    def _on_exit(payload: None):
        assert True
    results = bus.stop()
    assert len(results) == 1


def test_empty_brodcast(bus: trolleybus.EventBus):
    results = bus.broadcast(TestEvent, 2)
    assert not results


def test_empty_send_one(bus: trolleybus.EventBus):
    with pytest.raises(trolleybus.NoListenersError):
        bus.send_one(TestEvent, 1)


def test_empty_send_any(bus: trolleybus.EventBus):
    result = bus.send_any(TestEvent, 1)
    assert result is None


def test_custom_event(bus: trolleybus.EventBus):
    @bus.subscribe(TestEvent)
    def _on_test_event(payload: int):
        assert payload == 1
        return payload * 2

    result = bus.send_one(TestEvent, 1)
    assert result == 2


def test_priority(bus: trolleybus.EventBus):
    @bus.subscribe(TestEvent, priority=60)
    def _low_priority(payload: int):
        return payload

    @bus.subscribe(TestEvent, priority=40)
    def _high_priority(payload: int):
        return payload * 2

    results = bus.broadcast(TestEvent, 2)
    assert len(results) == 2
    assert results[0] == 4
    assert results[1] == 2


def test_send_one(bus: trolleybus.EventBus):
    @bus.subscribe(TestEvent, priority=60)  # type: ignore
    def _low_priority(payload: int):
        assert False, 'Should not be called'

    @bus.subscribe(TestEvent, priority=40)
    def _high_priority(payload: int):
        return payload * 2

    result = bus.send_one(TestEvent, 2)
    assert result == 4


def test_send_any(bus: trolleybus.EventBus):
    @bus.subscribe(TestEventOptional, priority=60)
    def _low_priority(payload: int):
        return payload

    @bus.subscribe(TestEventOptional, priority=40)
    def _high_priority(payload: int):
        return None

    result = bus.send_any(TestEventOptional, 2)
    assert result == 2


def test_error_handling_broadcast(bus: trolleybus.EventBus):
    @bus.subscribe(TestEventOptional, priority=60)  # type: ignore
    def _low_priority(payload: int):
        assert False, 'Should not be called'

    @bus.subscribe(TestEventOptional, priority=40)  # type: ignore
    def _high_priority(payload: int):
        raise RuntimeError()

    with pytest.raises(RuntimeError):
        bus.broadcast(TestEventOptional, 2)


def test_subscriber(bus: trolleybus.EventBus):
    class TestSubscriber(trolleybus.Subscriber):
        @trolleybus.subscribe(TestEvent)
        def on_test_event(self, payload: int):
            return payload * 2

    subscriber = TestSubscriber(bus)
    bus.start()
    result = bus.send_one(TestEvent, 2)
    assert result == 4


def test_emitter(bus: trolleybus.EventBus):
    class TestSubscriberEmitter(trolleybus.Subscriber, trolleybus.EmitterMixin):
        @trolleybus.subscribe(TestEvent)
        def on_test_event(self, payload: int):
            return payload * 2

    subscriber = TestSubscriberEmitter(bus)
    bus.start()
    result = subscriber.send_one(TestEvent, 2)
    assert result == 4
