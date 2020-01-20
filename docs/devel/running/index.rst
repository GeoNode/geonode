How to run GeoNode Core for development
=======================================


In order to start Geonode Core for development, you need to make sure that no Geonode instance is running first. This can be done by running the following commands:

.. code-block:: shell
    
    $ cd /home/user/geonode
    
    $ paver stop_geoserver
    
    $ paver stop_django
    
Then you need to start both geoserver and django services as follows:

.. code-block:: shell
    
    $ paver start_geoserver
    
    $ paver start_django

Now you can visit your Geonode GUI by typing http://localhost:8000 into your browser window



How to run GeoNode Project for development
===========================================


In order to run a project for development, the following steps have to be followed:

1- Make sure there is no running instance of Geonode first by running the following command:

.. code-block:: shell
    
    $ cd /home/user/my_geonode 
    
    $ paver stop

The above command will stop all services related to Geonode if running

2- Start the servers by running paver start as follows:

.. code-block:: shell
    
    $ paver start

Now you can visit your geonode project site by typing http://localhost:8000 into your browser window
