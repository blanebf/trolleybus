trolleybus
==========

trolleybus is a small publish/subscribe event bus with typed events,
inspired by the CherryPy bus.

Events are plain classes that carry the payload type and the listener
return type, so event payloads and results can be statically checked
with mypy (the package ships a ``py.typed`` marker):

.. code-block:: python

    import trolleybus

    class UserLoggedIn(trolleybus.Event[str, None]):
        pass

    bus = trolleybus.EventBus()

    @bus.subscribe(UserLoggedIn)
    def greet(username: str) -> None:
        print(f'Hello, {username}!')

    bus.broadcast(UserLoggedIn, 'kate')

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   intro
   tutorial
   reference

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
