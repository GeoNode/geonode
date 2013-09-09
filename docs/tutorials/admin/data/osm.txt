.. _osm2pgsql:

Loading OSM Data into GeoNode
=============================

In this section, we will walk through the steps necessary to load OSM data into your GeoNode project. As discussed in previous sections, your GeoNode already uses OSM tiles from MapQuest and the main OSM servers as some of the available base layers. This session is specifically about extracting actual data from OSM and converting it for use in your project and potentially for Geoprocessing tasks.

The first step in this process is to get the data from OSM. We will be using the OSM Overpass API since it lets us do more complex queries than the OSM API itself. You should refer to the OSM Overpass API documentation to learn about all of its features. It is an extremely powerful API that lets you extract data from OSM using a very sophisticated API. 

- http://wiki.openstreetmap.org/wiki/Overpass_API
- http://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide

In this example, we will be extracting building footprint data around Port au Prince in Haiti. To do this we will use an interactive tool that makes it easy construct a Query against the Overpass API. Point your browser at http://overpass-turbo.eu/ and use the search tools to zoom into Port Au Prince and Cite Soleil specifically. 

You will need to cut and paste the query specified below to get all of the appropriate data under the bbox::

    <osm-script>
      <union into="_">
        <bbox-query {{bbox}}/>
        <recurse into="x" type="node-relation"/>
        <query type="way">
          <bbox-query {{bbox}}/>
          <has-kv k="building" v="yes"></has-kv>
        </query>
        <recurse into="x" type="way-node"/>
        <recurse type="way-relation"/>
      </union>
      <print mode="meta"/>
    </osm-script>

This should look like the following.

.. figure:: img/overpass_turbo.png

When you have the bbox and query set correctly, click the "Export" button on the menu to bring up the export menu, and then click the API interpreter link to download the OSM data base on the query you have specified. 

.. figure:: img/overpass_export.png

This will download a file named 'interpreter' on your file system. You will probably want to rename it something else more specific. You can do that by issuing the following command in the directory where it was downloaded::

    $ mv interpreter cite_soleil_buildings.osm

.. note:: You can also rename the file in your Operating Systems File managmenet tool (Windows Explorer, Finder etc).

Now that we have osm data on our filesystem, we will need to convert it into a format suitable for uploading into your GeoNode. There are many ways to accomplish this, but for purposes of this example, we will use an OSM QGIS plugin that makes if fairly easy. Please consult the wiki page that explains how to install this plugin and make sure it is installed in your QGIS instance. Once its installed, you can use the Web Menu to load your file.

.. figure:: img/load_osm.png

This will bring up a dialog box that you can use to find and convert the osm file we downloaded.

.. figure:: img/load_osm_dialog.png

When the process has completed,  you will see your layers in the Layer Tree in QGIS.

.. figure:: img/qgis_layers.png

Since we are only interested in the polygons, we can turn the other 2 layers off in the Layer Tree.

.. figure:: img/qgis_layer_off.png

The next step is to use QGIS to convert this layer into a Shapefile so we can upload it into GeoNode. To do this, select the layer in the Layer tree, right click and then select the Save As option.

.. figure:: img/qgis_save_as.png

This will bring up the Save Vector Layer as Dialog.

.. figure:: img/qgis_save_as_dialog.png

Specify where on disk you want your file saved, and hit Save then OK.

.. figure:: img/save_layer_path.png

You now have a shapefile of the data you extracted from OSM that you can use to load into GeoNode. Use the GeoNode Layer Upload form to load the Shapefile parts into your GeoNode, and optionally edit the metadata and then you can view your layer in the Layer Info page in your geonode.

.. figure:: img/buildings_layer_geonode.png

.. note:: You may want to switch to an imagery layer in order to more easily see the buildings on the OSM background.
