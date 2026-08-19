Tutorial
========

This tutorial builds a small example application around the event bus: a
service that announces user logins and resolves configuration values. All
snippets are runnable as-is.

Defining events
---------------

An event is a subclass of :class:`~trolleybus.Event` parameterized with the
payload type passed to the listeners and the type of the value they return:

.. code-block:: python

    import trolleybus

    class UserLoggedIn(trolleybus.Event[str, None]):
        """payload: username, listeners return nothing"""

    class ResolveConfig(trolleybus.Event[str, dict]):
        """payload: config key, listeners return the resolved value"""

Events are never instantiated — the class itself *is* the event. If no
``name`` is given, the class name is used.

Emitting your first event
-------------------------

Create an event bus and subscribe a listener. The ``subscribe`` method works
both as a decorator and in its direct form:

.. code-block:: python

    bus = trolleybus.EventBus()

    @bus.subscribe(UserLoggedIn)
    def greet(username: str) -> None:
        print(f'Hello, {username}!')

    def audit(username: str) -> None:
        print(f'audit: {username} logged in')

    bus.subscribe(UserLoggedIn, audit)

    bus.broadcast(UserLoggedIn, 'kate')
    # Hello, kate!
    # audit: kate logged in

:meth:`~trolleybus.EventBus.broadcast` calls every listener with the payload
and returns their results as a list. If a listener raises an exception, the
error is logged, re-raised and the remaining listeners are not called.

Subscribing the same listener twice only updates its priority.

Priorities and unsubscribing
----------------------------

Listeners run in descending priority order (the default is
:data:`~trolleybus.DEFAULT_PRIORITY`, 50); listeners with equal priority run
in subscription order:

.. code-block:: python

    @bus.subscribe(UserLoggedIn, priority=60)
    def greet_first(username: str) -> None:
        ...

    bus.broadcast(UserLoggedIn, 'kate')  # greet_first runs before greet

To remove a listener, call :meth:`~trolleybus.EventBus.unsubscribe`;
removing an unknown listener is a silent no-op:

.. code-block:: python

    bus.unsubscribe(UserLoggedIn, audit)

Handling listener errors
------------------------

Use :meth:`~trolleybus.EventBus.broadcast_nothrow` when every listener must
run even if one of them fails. Errors are captured in
:class:`~trolleybus.ListenerResult` items instead of being raised:

.. code-block:: python

    @bus.subscribe(UserLoggedIn)
    def flaky(username: str) -> None:
        raise RuntimeError('oops')

    for result in bus.broadcast_nothrow(UserLoggedIn, 'kate'):
        if not result.ok:
            print('listener failed:', result.error)
        else:
            print('listener returned:', result.value)

Request/response: send_one
--------------------------

:meth:`~trolleybus.EventBus.send_one` delivers the event only to the
listener with the highest priority and returns its result. This turns the
bus into a pluggable request/response mechanism:

.. code-block:: python

    CONFIG = {'database.url': {'driver': 'sqlite'}}

    @bus.subscribe(ResolveConfig)
    def resolve(key: str) -> dict:
        return CONFIG[key]

    config = bus.send_one(ResolveConfig, 'database.url')

If no listener is subscribed to the event,
:exc:`~trolleybus.NoListenersError` is raised.

Fallback chains: send_any
-------------------------

:meth:`~trolleybus.EventBus.send_any` calls listeners in order until one of
them returns a value other than `None`, which makes it easy to chain
fallbacks:

.. code-block:: python

    @bus.subscribe(ResolveConfig, priority=60)
    def resolve_from_env(key: str) -> dict | None:
        ...  # returns None when the environment has no answer

    @bus.subscribe(ResolveConfig, priority=50)
    def resolve_from_defaults(key: str) -> dict | None:
        return {'driver': 'sqlite'}

    config = bus.send_any(ResolveConfig, 'database.url')

If all listeners return `None` (or there are no listeners), `None` is
returned.

Bus lifecycle
-------------

The bus itself emits events when it starts and stops:

.. code-block:: python

    @bus.subscribe(trolleybus.OnStart)
    def on_start(_: None) -> None:
        print('components are starting')

    @bus.subscribe(trolleybus.OnExit)
    def on_exit(_: None) -> None:
        print('components are shutting down')

    bus.start()  # emits OnStart, then OnStarted
    bus.stop()   # emits OnExit

``stop`` never raises: ``OnExit`` listener errors are captured as
:class:`~trolleybus.ListenerResult` items so every listener gets a chance to
shut down.

Class-based subscribers
-----------------------

Groups of related handlers can be bundled into a
:class:`~trolleybus.Subscriber`. Methods decorated with
:func:`~trolleybus.subscribe` are attached to the bus when it starts and
detached when it stops, so a subscriber survives any number of start/stop
cycles:

.. code-block:: python

    class Metrics(trolleybus.Subscriber):
        @trolleybus.subscribe(UserLoggedIn)
        def on_user_logged_in(self, username: str) -> None:
            print(f'metrics: {username} logged in')

    metrics = Metrics(bus)
    bus.start()  # handlers attach
    bus.broadcast(UserLoggedIn, 'kate')
    bus.stop()   # handlers detach; they re-attach on the next start
    bus.start()  # handlers attach again

Emitters
--------

Components that only publish events can use the
:class:`~trolleybus.EmitterMixin` facade, which exposes the emission
shortcuts of the bus:

.. code-block:: python

    class LoginService(trolleybus.Subscriber, trolleybus.EmitterMixin):
        def login(self, username: str) -> None:
            self.broadcast(UserLoggedIn, username)

    service = LoginService(bus)
    bus.start()
    service.login('kate')

A standalone emitter also exists: ``emitter = trolleybus.Emitter(bus)``.

Next steps
----------

The :doc:`reference` covers the complete public API in detail.
