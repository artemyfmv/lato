.. _message_composition:

Message Composition and Decomposition
=====================================

If there are multiple command handlers (i.e. in different modules) for the same Command, all handlers for that
command will be executed (decomposition), and the results of command handlers will be merged into single response
(composition).

.. literalinclude:: ../../examples/example5.py

By default, handler responses of type ``dict`` will be recursively merged into a single dict, and responses of type 
``list`` will be merged a into single list.


You can use ``Application.compose`` decorator to declare a custom composer. A custom composer will receive kwargs
with names of the modules handling the response.

.. literalinclude:: ../../examples/example6.py

