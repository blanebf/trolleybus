API reference
=============

All public names are exported by the top-level :mod:`trolleybus` package.

.. automodule:: trolleybus

Events
------

.. autoclass:: trolleybus.Event

.. autoclass:: trolleybus.OnStart

.. autoclass:: trolleybus.OnStarted

.. autoclass:: trolleybus.OnExit

Event bus
---------

.. autoclass:: trolleybus.EventBus
   :members:
   :member-order: bysource

.. autoclass:: trolleybus.ListenerResult
   :members:

.. autoexception:: trolleybus.NoListenersError

.. data:: DEFAULT_PRIORITY
   :value: 50

   Default priority assigned to listeners by :meth:`~trolleybus.EventBus.subscribe`
   and :func:`~trolleybus.subscribe`. Listeners with a higher priority value
   run first.

Subscribers
-----------

.. autoclass:: trolleybus.Subscriber
   :members:
   :member-order: bysource

.. autofunction:: trolleybus.subscribe

Emitters
--------

.. autoclass:: trolleybus.Emitter

.. autoclass:: trolleybus.EmitterMixin
   :members:
   :member-order: bysource
