.. _core_exercises:

Exercises
=========

Shell and Utilities
...................

#. *ssh* into your virtual machine or other instance
#. *sudo* to modify the *sshd_config* settings to verify disabling of dns resolution (UseDNS=no)
#. install a command line helper

  .. code-block:: console

    $ sudo apt-get install bash-completion

#. exercise command completion

  .. code-block:: console

    $ apt-get install <TAB><TAB>

#. activate/deactivate the *virtualenv* on your instance

  .. code-block:: console

    $ source /var/lib/geonode/bin/activate
    $ deactivate

#. set the *DJANGO_SETTINGS_MODULE* env variable

  .. code-block:: console

    $ export DJANGO_SETTINGS_MODULE=geonode.settings

#. install the *httpie* utility via pip

  .. code-block:: console

    $ pip install httpie
    $ http http://localhost/geoserver/rest
    $ http -a admin http://localhost/geoserver/rest
    <type in password - geoserver>

Python
......

#. launch *ipython* and experiment

  .. code-block:: python

    > x = "some text"
    > x.<TAB><TAB>
    > x.split.__doc__
    > ?

#. execute a script with *ipython* and open the REPL

  .. code-block:: console

    $ echo "twos = [ x*2 for x in range(5)]" > test.py
    $ ipython -i test.py
    > twos



  


