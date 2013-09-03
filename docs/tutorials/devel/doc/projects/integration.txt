.. _projects.integration:

Integrating your project with other systems
===========================================

Your GeoNode project is based on core components which are interoperable and as such, it is straightforward for you to integrate with external applications and services. This section will walk you through how to connect to your GeoNode instance from other applications and how to integrate other services into your GeoNode project. When complete, you should have a good idea about the possibilities for integration, and have basic knowledge about how to accomplish it. You may find it necessary to dive deeper into how to do more complex integration in order to accomplish your goals, but you should feel comfortable with the basics, and feel confident reaching out to the wider GeoNode community for help.

OGC services
------------

Since GeoNode is built on GeoServer which is heavily based on OGC services, the main path for integration with external services is via OGC Standards. A large number of systems, applications and services support adding WMS layers to them, but only a few key ones are covered below. WFS and WCS are also supported in a wide variety of clients and platforms and give you access to the actual data for use in GeoProcessing or to manipulate it to meet your requirements. GeoServer also bundles GeoWebCache which produces map tiles that can be added as layers in many popular web mapping tools including Google Maps, Leaflet, OpenLayers and others. You should review the reference material included in the first chapter to learn more about OGC Services and when evaluating external systems make sure that they are also OGC Compliant in order to integrate as seamlessly as possible.  

ArcGIS
------

ArcGIS Desktop (ArcMap) supports adding WMS layers to your map project. The following set of steps will walk you through how to configure a WMS Layer from your GeoNode within ArcMap.

First, you can start with a new empty project or add these layers to your existing project.

.. figure:: img/arcmap_empty.png

Next click the ArcCatalog button on the toolbar to bring up its interface.

.. figure:: img/arccatalog.png

From there, double click the "Add WMS Server" item in the tree to bring up the dialog that lets you enter the details for your WMS.

.. figure:: img/arc_add_wms.png

Next, enter the URL for your GeoNode's WMS endpoint which is the base url with /geoserver/wms appended to the end of the URL. You can also enter your credentials into the optional Account section of this dialog to gain access to non-public layers that your user may have access to.

.. figure:: img/arc_enter_wms_url.png

Click the "Get Layers" button to ask ArcMap to query your WMS's GetCapabilities document to get the list of available layers.

.. figure:: img/arcmap_wms_layers.png

After you click the OK button, your GeoNode layers will appear in the ArcCatalog Interface.

.. figure:: img/arcmap_layers_catalog.png

Once your server is configured in ArcMap, you can right click on one of the layers and investigate its properties.

.. figure:: img/arcmap_layer_properties.png

In order to actually add the layer to your project, you can drag and drop it into the Table of Contents, or right click and select "Create Layer". Your Layer will now be displayed in the map panel of your project.

.. figure:: img/arcmap_wms_layer_drag.png

.. figure:: img/arcmap_wms_layer_map.png

Once the layer is in your projects Table of Contents, you can right click on it and select the Layer Properties option and select the Styles Tab to choose from the available styles for that layer.

.. figure:: img/arcmap_wms_styles.png


Now that we have seen how to add a WMS layer to our ArcMap project, lets walk through how to add the same layers as a WFS which retrieves the actual feature data from your GeoNode rather than a rendered map as you get with WMS. Adding layers as a WFS gives you more control over how the layers are styled within ArcMap and makes them available for you to use with other ArcGIS tools like the Geoprocessing toolbox.

.. note:: Adding WFS layers to ArcMap requires that you have the Data Interoperability Extension installed. This extension is not included in ArcMap by default and is licensed and installed separately.

Start by opening up the ArcCatalog Interface within ArcMap and make sure that you have the "Interoperability Connections" option listed in the list. 

.. figure:: img/arcmap_interoperability.png

Next select "Add Interoperability Connection" to bring up the dialog that lets you add the WFS endpoint from your GeoNode.

.. figure:: img/arcmap_interop_add.png

Select "WFS (Web Feature Service)" in the Format dropdown and enter the URL to the WFS endpoint for your GeoNode in the Dataset field. The WFS endpoint is your base URL + /geoserver/wfs

.. figure:: img/arcmap_interop_wfs.png

You will need to click the "Parameters" button to supply more connection information including your credentials which will give you the ability to use private layers that you have access to. 

.. figure:: img/arcmap_wfs_params.png

Select the Feature Types button to have ArcMap get a list of layers from the WFS Service of your GeoNode. 

.. figure:: img/arcmap_wfs_layers.png

Select the layers that you want to add and click OK and ArcMap will import the features from your GeoNode into the system.

.. figure:: img/arcmap_wfs_import.png

Depending on the projection of your data, you may receive a warning about Alignment and Accuracy of data transformations. You can specify the transformation manually or simply hit close to ignore this dialog. If you dont want to be warned again, use the checkboxes in this dialog to hide these warnings temporarily or permanently.

.. figure:: img/arcmap_wfs_transformations.png

Your WFS Layer will be added to your map and you can view it in the Map Panel. If you need to, use the "Zoom to Layer Extent" or other zoom tools to zoom to the bounds of your layer.

.. figure:: img/arcmap_wfs_layer_view.png

You can now use the identify tool to inspect a feature in your layer, or perform any other function that you can normally use to work with Vector Layers in ArcMap.

.. figure:: img/arcmap_wfs_identify.png

Since your layer was imported as actual vector features, you can use normal ArcMap styling tools to style the layer to match how you want it to be displayed.

.. figure:: img/arcmap_wfs_style.png

Now that you have added layers from your GeoNode as both WMS and WFS, you can explore the other options available to you with these layers within ArcMap. 

QGIS
----

Quantum GIS or qGIS is an open source, cross platform desktop GIS app. It can also be used to add layers from your GeoNode instance as WMS or WFS. The process is very similar to how we add these same layers to ArcMap, and we will walk through the steps necessary in the following section.

First, select "Add WMS Layer" from the Layer menu.

.. figure:: img/qgis_add_wms_layer.jpg

The Add WMS Layer Dialog will be displayed where you are able to specify the parameters to connect to your WMS server. 

.. figure:: img/qgis_wms_add_1.jpg

Next, you need to fill in the parameters to connect to your GeoNode instance. The URL for your GeoNode's WMS is the base URL + /geoserver/wms 

.. figure:: img/qgis_wms_add_2.jpg

After clicking the OK button, your server will show up in the list of servers. Make sure its selected, then, click the connect button to have QGIS retrieve the list of layers from your GeoNode.

.. figure:: img/qgis_wms_add_7.jpg

Select the layers you want to add to your QGIS project and click "Add".

.. figure:: img/qgis_wms_add_6.jpg

Your layer will be displayed in the map panel.

.. figure:: img/qgis_wms_layer.jpg

You can then zoom into your features in the Map.

.. figure:: img/qgis_wms_layer_zoom.jpg

From there, you can use the identify tool to inspect the attributes of one of the features on the map.

.. figure:: img/qgis_identify_wfs.jpg

Or, you can look at the layer metadata by right clicking on the layer and selecting Layer Properties and selecting the metadata tab.

.. figure:: img/qgis_wms_metadata.jpg

Adding WFS servers and layers to your QGIS project is very similar to adding WMS. Depending on your version of QGIS, you may need to add the WFS plugin. You can use the Plugin manager to add it.

.. figure:: img/qgis_wfs_installer.jpg

Once the plugin is installed, you can select the "Add WFS Layer" option from the Layer menu.

.. figure:: img/qgis_add_wfs.jpg

Step through the same process you did for WMS to create a new WFS connection. First specify server parameters and click OK.

.. figure:: img/qgis_wfs_add_2.jpg

Then click Connect to retrieve the list of layers on the server and select the layers you want to add and click Apply.

.. figure:: img/qgis_wfs_add_3.jpg

The layer(s) you selected will be displayed in the map panel.

.. figure:: img/qgis_wfs_layer.jpg

You can use the same identify tool to inspect features in the map panel.

.. figure:: img/qgis_wfs_identify.jpg

To look at more information about your layer, right click the layer in the Table of Contents and select Layer Properties. You can look at the list of fields.

.. figure:: img/qgis_wfs_fields.jpg

... or set a style to match how you want your data to be displayed.

.. figure:: img/qgis_wfs_style.jpg

You now know how to add layers from your GeoNode instance to a QGIS project. You can explore all of the other options available to you in QGIS by consulting its documentation.

Google Earth
------------

GeoNode's built in map interface lets you look at your layers and maps in the Google Earth plugin directly in your browser. You can switch to this 3D viewer directly in GeoNode by clicking the google earth icon in the map panel.

.. figure:: img/ge_layer.png

GeoServer will render your layer as an image until you are zoomed in sufficiently, and then it will switch to rendering it as a vector overlay that you can click on to view the attributes for the feature you clicked on.

.. figure:: img/ge_feature_info.png

You can also use this option in the GeoExplorer client by clicking the same button.

.. figure:: img/ge_geoexplorer.png

.. note:: Some of the GeoExplorer options will not be available to you when you are in this mode, they will be grayed out an inaccessible.

If instead you want to use layers from your GeoNode in the Google Earth client itself, you have a few options available to you.

First, you can select the KML option from the Download Layer menu to download the entire layer in a single KML file. Depending on the size of the layer, your GeoNode could take several seconds or longer to generate this KML and return it to you. 

.. figure:: img/download_kml.png

When the layer is generated, it will be downloaded to your desktop machine and you can simply double click it to open it in Google Earth.

.. figure:: img/google_earth.png

Alternatively, you can use the "View in Google Earth" option in the Layer Download menu to view the layer in Google Earth using the same methodology described above depending on the zoom level. 

.. figure:: img/download_kmz.png

This will download a small KMZ to your desktop that contains a reference to the layers on the server and you can double click it to open it in Google Earth. 

.. figure:: img/kmz_ge.png

.. note:: The basic difference between these two options is that the first downloads *all* of the data to your desktop at once and as such, the downloaded file can be used offline while the second is simply a Network Link to the layer on the server. Choose whichever method is best for your own needs and purposes.

Once you have added your layers to the Places panel in Google Earth, you can move them from the Temporary Places section into My Places if you wish to use them after your current Google Earth session is complete. You can arrange them in folders and use Google Earth functionality to save your project to disk. Consult Google Earths documentation for more information about how to do this.

OpenStreetMap
-------------

Data from OpenStreetMap is used to generate the map tiles which are the default base layer in your GeoNode. These are provided by MapQuest and are reasonably current with recent edits to the OpenStreetMap database. You can switch to an alternate set of map tiles by changing your base layer. 

.. figure:: img/osm_layers.png

If you would like to change the default base layer to use the alternate OSM tile set, you can change this in the settings.py file for your project. In the MAP_BASELAYERS dictionary, set the visibility setting to True for the gxp_olsource and False for the gxp_mapquestsource. 

.. figure:: img/change_osm.png

If instead of map tiles, you would like to work with OSM database itself, you should consult the section titled "Loading OSM Data into GeoNode" in this workshop.
