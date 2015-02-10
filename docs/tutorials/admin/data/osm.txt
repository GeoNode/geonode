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

This will download a file named 'export.osm' on your file system. You will probably want to rename it something else more specific. You can do that by issuing the following command in the directory where it was downloaded::

    $ mv export.osm cite_soleil_buildings.osm

.. note:: You can also rename the file in your Operating Systems File management tool (Windows Explorer, Finder etc).

Exporting OSM data to shapefile using QGIS
------------------------------------------

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

Exporting OSM data to shapefile using GDAL
------------------------------------------

An alternative way to export the .osm file to a shapefile is to use `ogr2ogr <http://www.gdal.org/ogr2ogr.html>`_ combined with the `GDAL osm driver <http://www.gdal.org/ogr/drv_osm.html>`_, available from GDAL version 1.10.

As a first step, inspect how the GDAL osm driver sees the .osm file using the ogrinfo command::

    $ ogrinfo cite_soleil_buildings.osm
    Had to open data source read-only.
    INFO: Open of `cite_soleil_buildings.osm'
          using driver `OSM' successful.
    1: points (Point)
    2: lines (Line String)
    3: multilinestrings (Multi Line String)
    4: multipolygons (Multi Polygon)
    5: other_relations (Geometry Collection)

ogrinfo has detected 5 different geometric layers inside the osm data source. As we are just interested in the buildings, you will just export to a new shapefile the multipolygons layer using the GDAL ogr2ogr command utility::

    $ ogr2ogr cite_soleil_buildings cite_soleil_buildings.osm multipolygons

Now you can upload the shapefile to GeoNode using the GeoNode Upload form in the same manner as you did in the previous section.

Using GeoGig to load OSM Data into Manage OSM Data
--------------------------------------------------

Another alternative for working with OSM data in your GeoNode is to use `GeoGig <http://geogig.org/>`_. GeoGig is a tool that draws inspiration from Git but adapts its core concepts to handle distributed versioning of geospatial data. GeoGig allows you to load OpenStreetMap data into a repository on your server and either export that data into PostGIS for use in your GeoNode, or configure the GeoGig GeoServer extension and expose the repo directly from GeoServer. An article about this process can be found on the `Boundless Geo Blog <http://http://boundlessgeo.com/2014/03/geogit-and-openstreetmap-for-yolanda/>`_. and will be described below. Much of the impetus for GeoGig came from the ROGUE JCTD and the technology has been incorporated into the `GeoSHAPE project <http://http://geoshape.org/>`_.

Much more information about how to perform the steps below can be found in the GeoGig documentation page on `Using GeoGig with OpenStreetMap data <http://geogig.org/docs/interaction/osm.html>`_. The instructions that follow are only a brief overview of the process.

Getting Started
+++++++++++++++

You will first need to install the GeoGig command line tools. These can be found on the projects `SourceForge page <http://sourceforge.net/projects/geogig/files/latest/download>`_. Follow the instructions contained in the installation file in order to install the CLI tools on your GeoNode server. Once you have the tools installed and added to your path, the *geogig* command should be available::

    $ geogig --version
             Project Version : 1.0-SNAPSHOT
                  Build Time : December 18, 2014 at 03:59:10 UTC
             Build User Name : Unknown
            Build User Email : Unknown
                  Git Branch : master
               Git Commit ID : a4a80a8dd853dfe497729b35399594947866e8ae
             Git Commit Time : December 18, 2014 at 03:44:24 UTC
      Git Commit Author Name : Gabriel Roldan
     Git Commit Author Email : gabriel.roldan@gmail.com
          Git Commit Message : Synchronize DefaultPlatform.getTempDir() to avoid false precondition check on concurrent access.

Once the geogig command is available, you will need to create an empty repository to hold your data. Change directories to a suitable location on your servers filesystem and issue the following command substituting *my_repo* for whatever name you choose::

    $ cd /somewhere/on/file/system
    $ mkdir my_repo
    $ geogig init
    Initialized empty Geogig repository in /somewhere/on/filesystem/my_repo/.geogig

Loading OSM Data into your Repository
+++++++++++++++++++++++++++++++++++++

Now that you have an empty repository to store our data, the next step is to load the current snapshot of OSM data into your repository using the *geogig osm download* command. At a minimum, you will want to use a bounding box filter to limit the downloaded data to the area of interest for your geonode installation. The example below is a bounding box that encompasses the country of Malawi. More information about the geogig osm download command can be found in the `geogig docs <http://geogig.org/manpages/osmdownload.html>`_.::

    $ geogig osm download --bbox -17.129459 32.668991 -9.364680 35.920441 --saveto ./mw-osm-temp --keep-files

    Connecting to http://overpass-api.de/api/interpreter...

    Downloaded data will be kept in /somewhere/on/filesystem/my_repo/./mw-osm-temp

    Importing into GeoGig repo...
    1,164,420
    1,164,420 entities processed in 5.892 min

    Building trees for [node, way]

    Trees built in 7.614 s
    0%
    Staging features...
    100%

    Committing features...
    100%
    Processed entities: 1,164,420.
     Nodes: 1,091,572.
     Ways: 72,848

GeoGig stores data in *trees* which are basically equivalent to *layers* in a normal geospatial context. At this point in the process, your repo contains 2 trees for *ways* and *nodes* from OSM. In order to convert these into layers that may be more familiar to your users like *roads*, *buildings* or *medical facilities*, you will need to apply a mapping that filters the complete list of nodes and ways and converts the tags into attributes. There are a great set of sample mappings in the US State Departments CyberGIS project. You can find them `here <https://github.com/state-hiu/cybergis-osm-mappings/tree/master/mappings>`_. You should clone this repository along side your geogig repository and then apply them as shown below::

    $ geogig osm map ../cybergis-osm-mappings/mappings/basic/buildings_and_roads.json

    $ geogig osm map ../cybergis-osm-mappings/mappings/health/medical_centers.json

    $ geogig osm map ../cybergis-osm-mappings/mappings/education/schools.json

Now you can inspect the repository using the following commands::

    $ geogig ls-tree
    osm_roads
    osm_buildings
    node
    way

    $ geogig show osm_roads
    TREE ID:  596a4f39ab9fadcbba6ffcaf5c135e29c2bc67d3
    SIZE:  20288
    NUMBER Of SUBTREES:  0
    DEFAULT FEATURE TYPE ID:  0f7cbc6c114727858fb50668eb8a4448667bdc12

    DEFAULT FEATURE TYPE ATTRIBUTES
    id: <LONG>
    geom: <LINESTRING>
    status: <STRING>
    media: <STRING>
    name: <STRING>
    ref: <STRING>
    highway: <STRING>
    lanes: <STRING>
    oneway: <STRING>
    surface: <STRING>
    access: <STRING>
    source: <STRING>
    motor_vehicle: <STRING>
    nodes: <STRING>

Updating the OSM Data in your Repository
++++++++++++++++++++++++++++++++++++++++

As OpenStreetMap is a constantly changing dataset, you will want to periodically update your repo with the latest changes from OSM. GeoGig provides a way to do this using the *geogig osm download* command with the --update flag::

    $ geogig osm download --update

.. note:: If you get an error that looks like the error below, this means that there are no changes in OSM since your last update and it can be ignored.

    Committing features...

    An unhandled error occurred: Nothing to commit after f249200302d5e808fb1b04f329b39b5853ffb7d0. See the log for more details.

Serving your GeoGig repository in GeoNode
+++++++++++++++++++++++++++++++++++++++++

At this point you have different options on how to serve this repository from your GeoNode. The most basic option is to *export* this data to PostGIS and configure the PostGIS database in GeoServer for use in GeoNode. First create a PostGIS database that will be used to store the data and then use the `geogig pg export command <http://geogig.org/manpages/pgexport.html>`_ to export the layers into this database for serving. Note you will need to replace the connection parameters below to match you r servers setup::

    $ geogig pg export --host localhost --port 5432 -- schema myschema --database my_osm_database --user my_user --password my_password osm_train_stations osm_train_stations

.. CAUTION::
   You may encounter an error when performing this step. This issue has been documented `here <https://github.com/boundlessgeo/GeoGig/issues/356>`_ and is being investigated by the GeoGig team. You will need to create a primary key metadata table as described `here <http://docs.geoserver.org/stable/en/user/data/database/primarykey.html>`_ and then follow the steps below. If you have questions about this process, please ask for help on the developers mailing list. 

Define your new primary key for the table we can't export (id is the osm id)::

    INSERT INTO gt_pk_metadata_table (table_schema, table_name, pk_column) VALUES ('geogig_data','osm_train_stations','id'); 

Next you need to alter your osm data table accordingly::

    ALTER TABLE geogig_data.osm_train_stations DROP CONSTRAINT osm_train_stations_pkey;

    ALTER TABLE geogig_data.osm_train_stations ADD PRIMARY KEY (id);

    ALTER TABLE geogig_data.osm_train_stations DROP COLUMN fid;

    ALTER TABLE geogig_data.osm_train_stations ADD COLUMN fid character varying(64);

Then you can run the *geogig pg export* command with the -o option to overwrite the table::

    $ geogig pg export -o --host localhost --port 5432 -- schema myschema --database my_osm_database --user my_user --password my_password osm_train_stations osm_train_stations

At this point, you need to configure your PostGIS database connection in GeoServer. More information about this process can be found in the `GeoServer documentation <http://docs.geoserver.org/stable/en/user/data/database/postgis.html>`_. 

Once the layers are configured in GeoServer. You want to issue the updatelayers to configure them in your GeoNode::

    $ python manage.py updatelayers --store geogig_data --filter osm_train_stations

Using the GeoGig GeoServer Extension
++++++++++++++++++++++++++++++++++++

The GeoGig project also contains a GeoServer extension that allows a GeoServer administrator to configure and serve the GeoGig store directly. This extension basically lets you treat your GeoGig repository as any other store of spatial data.

.. note:: This section is still to be completed.
