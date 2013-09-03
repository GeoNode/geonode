.. _sextante:

Spatial Processing with Sextante
================================

Once you have connected to a GeoNode service and its data is available from QGIS, analysis can be performed on it, just as if you were using local data.

SEXTANTE is the analysis and data processing framework of QGIS, and it can be used to run a large number of different analysis algorithms for both raster and vector data. Both WCS and WFS connections can be used to get data that can be processes through SEXTANTE.

The SEXTANTE toolbox is the main component to call processing algorithms, and it contains a list all of available ones, organized by providers. 

.. image:: img/toolbox.png


The *QGIS algorithms* group contains native python algorithms. Most of the remaining ones represent algorithms that depend on a third-party application. From the point of view of the user, however, there is no difference in the way these algorithms are executed, since they share a common UI and SEXTANTE takes care of the communication between the application and QGIS.

To run an algorithm, just click on its name in the toolbox, and a dialog will appear to define the inputs and outputs of the selected algorithm.

.. image:: img/centroids.png


All dialogs used to entering the parameters needed for an algorithm are created on-the-fly, and they all share the same look and feel, no matter which application the algorithm relies on.

If the selected algorithm requires vector layers, all loaded vector layers will be available, including those from WFS connections. If it requires raster layers, all loaded raster layers will be available, including those from WCS connections.

Click on *Ok* and the algorithm will be run and its outputs loaded in the QGIS canvas.

Algorithm depending on third-party application can be called in the same way. WFS and WMS layers will be available as well, even if the application does not support web services. SEXTANTE will take care of creating an intermediate file or selecting a compatible way of feeding the data into the application, performing all necessary import operations under the hood.

For instance, you can run algorithm that uses the R statistical computing software to perform a statistical analysis on the data loaded from a WFS connection.

.. image:: img/r_alg.png

The interface to define the input parameters is very similar to the one we saw in the previous example (and to those of all the other algorithms), and using an external application makes no difference from the point of view of the user.

.. image:: img/r_dialog.png

SEXTANTE algorithms are aware of the state of layers used for input. That means that they can take into account whether there is a selection in a vector layer, even in the case of calling an external application. In the SEXTANTE configuration menu, in the *General* group, check the "Use selected features" option to enable this behavior.

image:: use_selected.png

Now you can make a selection and call the R algorithm used before. It will just use those features that you selected. 

Notice that SEXTANTE provides the context for seamlessly integrating all the pieces and allowing to easily work with all of them together. In this case, GeoServer is providing the data, QGIS is providing the interface where we perform the selection, and R is providing the processing. SEXTANTE is just the mediator between these elements.

Using SEXTANTE we can interact with a GeoServer instance not just to consume its data, but to import into it, having a bidirectional connection.

In the *GeoServer/PostGIS tools* group, you will find some tools that you can use to create a new workspace, import a layer or import a style, among others. 

.. image:: img/geoserver.png

Styles are imported using an SLD file. Since QGIS supports exporting the style of a layer to SLD, you can create you styling using QGIS, then export it, and then use the corresponding SEXTANTE algorithm to add it to your GeoServer. To create and export a style, just right-click on a layer name in the TOC, select *Properties*, and then move to the *Style* tab. Clink on *Save Style..." and the select *SLD style*.

.. image:: img/style.png

Calling algorithms from the toolbox is the most common way of processing data with SEXTANTE, but in some cases that might not be the best alternative, specially if we have a workflow that involves a large number of different processes. SEXTANTE includes a graphical modeler that allow to create complex workflows that can be later executed as a single process, thus simplifying the process.

The modeler interface is started from the SEXTANTE menu, using the "SEXTANTE modeler" menu.

.. image:: img/modeler.png

Creating a model involves adding a set of inputs and then the algorithms to use on then, defining the links between them.

As an example, the model in the figure below takes a points layer, interpolates a raster layer from it and then extracts contour lines for that resulting raster layer, given an interval. The final layer is imported into a GeoServer instance. Used with a WFS service, this can be used to easily create an additional lines layer for a given points layer in a GeoServer instance, such as one containing temperature data for a set of sensors.

.. image:: img/model.png

The model can be added to the toolbox and run as any of the built-in algorithms. 

.. image:: img/model_toolbox.png

Its parameters dialog is also created automatically from the inputs it takes and the outputs it produces.

.. image:: img/model_dialog.png

SEXTANTE exposes its API through the QGIS python console, including not just all its available algorithms, but also several tools for easy handling both vector and raster data and creating new geoalgorithms. Users familiar with python will be able to create much more complex models with ease, and to automate tasks that involve processing.

algorithms are executed ussing the ``runalg`` method, passing the name of the algorithm and the parameters it requires. Importing a layer into geoserver can be done from the QGIS console using code like the one shown below:

::

	import sextante
	filename = "/home/gisdata/example.shp"
	sextante.runalg("gspg:importvectorintogeoserver","http://localhost:8080/geoserver/rest","admin","geoserver",filename,"workspace_name")

Algorithms in the ``gspg`` namespace include utilities for interacting with both GeoServer and PostGIS.

If the layer is loaded into QGIS, there is no need to enter the filename. The layer object can be obtained with the ``getobject()`` method and then passed to the algorithm call instead of the filename. For a layer named *mylayer*, that would be:

::

	import sextante
	layer = sextante.getobject("mylayer")
	sextante.runalg("gspg:importvectorintogeoserver","http://localhost:8080/geoserver/rest","admin","geoserver",layer,"workspace_name")


Finally, a last productivity tool is available in SEXTANTE: the batch processing interface. Repeated calls to a single algorithm are simplified by using the batch processing interface. This can be used, for instance, to perform a bulk import of layers into GeoServer, by setting the batch processing interface to call the *Import into GeoServer* algorithm as many times as layers are to be imported. 

To open the batch processing interface, right-click on the name of an algorithm in the toolbox and select *Run as batch process*.

.. image:: img/batch.png

Each row in the table (3 by default) represents a single execution, and more rows can be added manually, or will be automatically added when selecting a set of input layers, each of them to be used as input in a different execution of the algorithm. 

.. image:: img/batch_import.png

Models can also be run as a batch process. The model defined above, which computed a set of contour lines from a points layer and imported the result into GeoServer, can be called repeatedly using the same input layer and different intervals, to get contour layers of different level of detail, suitable to be rendered at different scales.

More detailed documentation about SEXTANTE can be found at a dedicated chapter in the current QGIS manual, at http://docs.qgis.org/html/en/docs/user_manual/sextante/index.html. For the most up-to-date version, check the corresponding entry at the QGIS documentation github repository, at https://github.com/qgis/QGIS-Documentation/tree/master/source/docs/user_manual/sextante
