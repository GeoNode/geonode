.. _all_together:

===================
Finish installation
===================

In previous sections you' ve setup all the applications we need to run GeoNode.

Test the installation
=====================

We are ready to restart GeoNode (Apache) and test the installation.
Restart Apache

.. code-block:: bash

    $ sudo service apache2 restart

Open the browser and navigate to http://localhost/

GeoNode User interface will show up. Login with admin username and password you
just set.

.. image:: img/test_geonode2.png
   :width: 600px
   :alt: Test GeoNode 2

.. image:: img/geonode_signin.png
   :width: 600px
   :alt: GeoNode admin signin

Now open the main menu and click on `GeoServer`

.. image:: img/access_geoserver.png
   :width: 600px
   :alt: GeoServer admin login

You will be redirected to GeoServer user interface. You will automatically be
logged in as administrator in GeoServer.

.. image:: img/geoserver_admin.png
   :width: 600px
   :alt: GeoServer Admin
