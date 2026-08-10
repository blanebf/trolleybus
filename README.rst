trolleybus
==========

Small publish/subscribe event bus with typed events, inspired by the
CherryPy bus.

Events are plain classes that carry the payload type and the listener
return type, so event payloads and results can be statically checked with
mypy (the package ships a ``py.typed`` marker).

.. code-block:: python

    import trolleybus

    class UserLoggedIn(trolleybus.Event[str, None]):
        pass

    bus = trolleybus.EventBus()

    @bus.subscribe(UserLoggedIn)
    def greet(username: str) -> None:
        print(f'Hello, {username}!')

    bus.broadcast(UserLoggedIn, 'kate')

Features
--------

- Typed event payloads and listener results (``Event[Payload, Result]``)
- Synchronous dispatch ordered by priority (higher value runs first,
  subscription order breaks ties)
- ``broadcast``, ``broadcast_nothrow``, ``send_one``, ``send_any`` emission
  styles
- Class-based ``Subscriber`` with declarative ``@subscribe`` handlers bound
  to the bus lifecycle (``OnStart`` / ``OnExit``)
- ``Emitter`` / ``EmitterMixin`` facades for components that only emit
- Thread-safe subscription management and broadcasting

Installation
------------

.. code-block:: console

    $ pip install trolleybus

Usage
-----

Events
~~~~~~

An event defines the payload type passed to the listeners and the type of
the value they return. Events are never instantiated.

.. code-block:: python

    import trolleybus

    class UserLoggedIn(trolleybus.Event[str, None]):
        """payload: username, listeners return nothing"""

    class ResolveConfig(trolleybus.Event[str, dict]):
        """payload: config key, listeners return the resolved value"""

If no ``name`` is given, the class name is used.

Subscribing
~~~~~~~~~~~

.. code-block:: python

    bus = trolleybus.EventBus()

    # decorator form
    @bus.subscribe(UserLoggedIn, priority=60)
    def greet(username: str) -> None:
        ...

    # direct form
    def audit(username: str) -> None:
        ...

    bus.subscribe(UserLoggedIn, audit, priority=40)
    bus.unsubscribe(UserLoggedIn, audit)

Subscribing the same listener twice only updates its priority.

Emitting
~~~~~~~~

.. code-block:: python

    # call all listeners, collect results, propagate listener errors
    bus.broadcast(UserLoggedIn, 'kate')

    # call all listeners, capture errors as ListenerResult(value, error)
    for result in bus.broadcast_nothrow(UserLoggedIn, 'kate'):
        if not result.ok:
            print('listener failed:', result.error)

    # call only the highest priority listener (NoListenersError if none)
    config = bus.send_one(ResolveConfig, 'database.url')

    # call listeners until one returns a non-None value
    config = bus.send_any(ResolveConfig, 'database.url')

The bus exposes two lifecycle events: ``bus.start()`` emits ``OnStart`` and
then ``OnStarted``, ``bus.stop()`` emits ``OnExit``.

Class-based subscribers
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class Metrics(trolleybus.Subscriber):
        @trolleybus.subscribe(UserLoggedIn)
        def on_user_logged_in(self, username: str) -> None:
            ...

    metrics = Metrics(bus)
    bus.start()  # handlers attach
    bus.stop()   # handlers detach; they re-attach on the next start

Emitters
~~~~~~~~

.. code-block:: python

    class LoginService(trolleybus.Subscriber, trolleybus.EmitterMixin):
        def login(self, username: str) -> None:
            self.broadcast(UserLoggedIn, username)

A standalone emitter also exists: ``emitter = trolleybus.Emitter(bus)``.

Development
-----------

.. code-block:: console

    $ poetry install
    $ poetry run pytest tests
    $ poetry run mypy trolleybus
    $ poetry run pylint trolleybus
