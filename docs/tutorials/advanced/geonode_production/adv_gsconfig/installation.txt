.. installation:

Installing the Monitoring Extension
===================================

Monitoring is an official extension, as such it can be found alongside any GeoServer release. The extension is split into two modules, "core" and "hibernate", where core provides the basic underpinnings of the module and allows to monitor "live" requests, while the hibernate extension provides database storage of the requests.

#. Get the monitoring zip files, already downloaded for you, from the training material ``data\plugins`` folder (search for zip files containing the ``monitoring`` word, there will be two)

#. Extract the contents of the archives into the ``<TRAINING_ROOT>/tomcat-6.0.36/instances/instance1/webapps/geoserver/WEB-INF/lib`` directory of the GeoServer installation.

Verifying the Installation
---------------------------

There are two ways to verify that the monitoring extension has been properly installed.

* Start GeoServer and open the `Web Administration interface <http://localhost:8083/geoserver>`_.  Log in using the administration account.  If successfully installed, there will be a :guilabel:`Monitor` section on the left column of the home page.

  .. figure:: img/monitorwebadmin.png
     :align: center

     *Monitoring section in the web admin interface*

* Start GeoServer and navigate to the current data directory.  If successfully installed, a new directory named ``monitoring`` will be created in the data directory.
