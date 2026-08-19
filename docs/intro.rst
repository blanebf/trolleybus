Introduction
============

trolleybus is a small publish/subscribe event bus with typed events.
Components publish *events*; any number of *listeners* subscribe to those
events and get called whenever the event is emitted. Events also serve as
loose coupling points: the emitter does not need to know its listeners, so
plugins and subsystems can react to each other without direct imports.

Unlike many messaging libraries, trolleybus is deliberately tiny: a single
event bus class, a few emission styles and a small amount of convenience
around lifecycle management — no external dependencies.

Typed events
------------

Every event declares two type parameters, ``Event[Payload, Result]``:

- ``Payload`` — the type of the value passed to every listener,
- ``Result`` — the type of the value listeners return.

Events are never instantiated; they only carry the types, a unique
identifier and a human-readable name. Because the payload and result types
are part of the event definition, both can be statically checked with mypy
(the package ships a ``py.typed`` marker).

Emission styles
---------------

The bus offers four ways to deliver an event, covering the common
publish/subscribe patterns:

- :meth:`~trolleybus.EventBus.broadcast` — call all listeners, collect their
  results, propagate the first listener error,
- :meth:`~trolleybus.EventBus.broadcast_nothrow` — call all listeners and
  capture per-listener errors as :class:`~trolleybus.ListenerResult` items,
- :meth:`~trolleybus.EventBus.send_one` — call only the highest-priority
  listener (request/response),
- :meth:`~trolleybus.EventBus.send_any` — call listeners until one returns a
  non-`None` value (fallback chain).

All dispatch is synchronous and ordered by priority: a higher priority value
runs first, subscription order breaks ties.

Lifecycle and integration
-------------------------

The bus exposes two lifecycle hooks, ``start`` and ``stop``, which emit the
built-in :class:`~trolleybus.OnStart`, :class:`~trolleybus.OnStarted` and
:class:`~trolleybus.OnExit` events. Class-based
:class:`~trolleybus.Subscriber` components use these hooks to attach and
detach their handlers automatically. Components that only emit events can
use the :class:`~trolleybus.Emitter` facade or
:class:`~trolleybus.EmitterMixin`.

Subscription management and broadcasting are thread-safe.

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
- No dependencies, ships a ``py.typed`` marker

Installation
------------

trolleybus requires Python 3.10 or newer.

.. code-block:: console

    $ pip install trolleybus

Where to go next
----------------

- The :doc:`tutorial` builds a small example application step by step.
- The :doc:`reference` lists the complete public API.
