.. _geoserver_data_config:

GeoServer Data Configuration
============================

While it is possible to import layers directly from your servers filesystem into your GeoNode, you may have an existing GeoServer that already has data in it, or you may want to configure data from a GeoServer which is not directly supported by uploading data.

GeoServer supports a wide range of data formats and connections to database, and while many of them are not supported as GeoNode upload formats, if they can be configured in GeoServer, you can add them to your GeoNode by following the procedure described below.

GeoServer supports 3 types of data: Raster, Vector and Databases. For a list of the supported formats for each type of data, consult the following pages:

- http://docs.geoserver.org/latest/en/user/data/vector/index.html#data-vector
- http://docs.geoserver.org/latest/en/user/data/raster/index.html
- http://docs.geoserver.org/latest/en/user/data/database/index.html

.. note:: Some of these raster or vector formats or database types require that you install specific plugins in your GeoServer in order to use the. Please consult the GeoServer documentation for more information.

Lets walk through an example of configuring a new PostGIS database in GeoServer and then configuring those layers in your GeoNode.

First visit the GeoServer administration interface on your server. This is usually on port 8080 and is available at http://localhost:8080/geoserver/web/

You should login with the superuser credentials you setup when you first configured your GeoNode instance.

Once you are logged in to the GeoServer Admin interface, you should see the following.

.. figure:: img/geoserver_admin.png

.. note:: The number of stores, layers and workspaces may be different depending on what you already have configured in your GeoServer.

Next you want to select the "Stores" option in the left hand menu, and then the "Add new Store" option. The following screen will be displayed.

.. figure:: img/geoserver_new_store.png

In this case, we want to select the PostGIS store type to create a connection to our existing database. On the next screen you will need to enter the parameters to connect to your PostGIS database (alter as necessary for your own database).

.. figure:: img/geoserver_postgis_params.png

.. note:: If you are unsure about any of the settings, leave them as the default.

The next screen lets you configure the layers in your database. This will of course be different depending on the layers in your database.

.. figure:: img/geoserver_publish_layers.png

Select the "Publish" button for one of the layers and the next screen will be displayed where you can enter metadata for this layer. Since we will be managing this metadata in GeoNode, we can leave these alone for now. 

.. figure:: img/geoserver_layer_params.png

The things that *must* be specified are the Declared SRS and you must select the "Compute from Data" and "Compute from native bounds" links after the SRS is specified.

.. figure:: img/geoserver_srs.png

Click save and this layer will now be configured for use in your GeoServer.

.. figure:: img/geoserver_layers.png

The next step is to configure these layers in GeoNode. The updatelayers management command is used for this purpose. As with importlayers, its useful to look at the command line options for this command by passing the --help option::

    $ python manage.py updatelayers --help

This help option displays the following::

    Usage: manage.py updatelayers [options] 

    Update the GeoNode application with data from GeoServer

    Options:
      -v VERBOSITY, --verbosity=VERBOSITY
                            Verbosity level; 0=minimal output, 1=normal output,
                            2=verbose output, 3=very verbose output
      --settings=SETTINGS   The Python path to a settings module, e.g.
                            "myproject.settings.main". If this isn't provided, the
                            DJANGO_SETTINGS_MODULE environment variable will be
                            used.
      --pythonpath=PYTHONPATH
                            A directory to add to the Python path, e.g.
                            "/home/djangoprojects/myproject".
      --traceback           Print traceback on exception
      -i, --ignore-errors   Stop after any errors are encountered.
      -u USER, --user=USER  Name of the user account which should own the imported
                            layers
      -w WORKSPACE, --workspace=WORKSPACE
                            Only update data on specified workspace
      --version             show program's version number and exit
      -h, --help            show this help message and exit

For this sample, we can use the default options. So enter the following command to configure the layers from our GeoServer into our GeoNode::

    $ python manage.py updatelayers

The output will look something like the following::

    [created] Layer Adult_Day_Care (1/11)
    [created] Layer casinos (2/11)
    [updated] Layer san_andres_y_providencia_administrative (3/11)
    [updated] Layer san_andres_y_providencia_coastline (4/11)
    [updated] Layer san_andres_y_providencia_highway (5/11)
    [updated] Layer san_andres_y_providencia_location (6/11)
    [updated] Layer san_andres_y_providencia_natural (7/11)
    [updated] Layer san_andres_y_providencia_poi (8/11)
    [updated] Layer san_andres_y_providencia_water (9/11)
    [updated] Layer single_point (10/11)
    [created] Layer ontdrainage (11/11)


    Finished processing 11 layers in 45.0 seconds.

    3 Created layers
    8 Updated layers
    0 Failed layers
    4.090909 seconds per layer

.. note:: This example picked up 2 additional layers that were already in our GeoServer, but were not already in our GeoNode.

For layers that already exist in your GeoNode, they will be updated and the configuration synchronized between GeoServer and GeoNode.

You can now view and use these layers in your GeoNode.

