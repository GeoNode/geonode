.. _python:

Debugging GeoNode's Python Components
=====================================


Logging
-------

References:

- http://docs.python.org/2/library/logging.html
- https://docs.djangoproject.com/en/1.4/topics/logging/

Logging is controlled by the contents of the logging data structure defined in
the :file:`settings.py`. The default settings distributed with GeoNode are
configured to only log errors. During development, it's a good idea to override
the logging data structure with something a bit more verbose.

Output
......

In production, logging output will go into the apache error log. This is located
in :file:`/var/log/apache2/error.log`. During development, logging output will,
by default, go to standard error.

Configuring
...........

* Ensure the 'console' handler is at the appropriate level. It will ignore log
  messages below the set level.
* Ensure the specific logger you'd like to use is set at the correct level.
* If attempting to log SQL, ensure ``DEBUG=True`` in your :file:`local_settings.py`.

Debugging SQL
.............

* To trace all SQL in django, configure the ``django.db.backends`` logger to
  ``DEBUG``
* To examine a specific query object, you can use the ``query`` field:
  str(Layer.objects.all().query)
* You can gather more information by using ``django.db.connection.queries``. When
  ``DEBUG`` is enabled, query SQL and timing information is stored in this list.

Hints
.....

* Don't use print statements. They are easy to use in development mode but in
  production they will cause failure.
* Take advantage of python. Instead of:

    .. code-block:: python

      logging.info('some var ' + x + ' is not = ' + y)

  Use:

    .. code-block:: python

      logging.info('some var %s is not = %s', x, y)

Excercises:
...........

#. Enable logging of all SQL statements. Visit some pages and view the logging output.
#. Using the python shell, use the ``queries`` object to demonstrate the results of specific queries.


PDB
---

Reference:

- http://docs.python.org/2/library/pdb.html

For the adventurous, ``pdb`` allows for an interactive debugging session. This
is only possible when running in a shell via ``manage.py runserver`` or
``paver runserver``.

To set a breakpoint, insert the following code before the code to debug.

  ..code-block:: python

    import pdb; pdb.set_strace()

When execution reaches this statement, the debugger will activate. The commands
are noted in the link above. In addition to those debugger specific commands,
general python statements are supported. For example, typing the name of a
variable in scope will yield the value via string coersion. Typing "n" will execute the next line, "c" wil continue the execution of the program, "q" will quit.
