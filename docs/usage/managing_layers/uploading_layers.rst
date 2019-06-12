.. _uploading-layers:

Layers Uploading
================

| The most important resource type in GeoNode is the *Layer*. A layer represents spatial information so it can be displayed inside a map.
| To better understand what we are talking about let's upload your first layer.

The *Layer Uploading* page can be reached from the :guilabel:`Upload Layer` link of the :guilabel:`Data` menu in the navigation bar.

.. figure:: img/upload_layer_link.png
     :align: center

     *Link for Layers Uploading*

There is also an :guilabel:`Upload Layers` button in the *Layers Page*.

.. figure:: img/upload_layer_link_from_list.png
     :align: center

     *Button for Layers Uploading*

The *Layers Uploading* page looks like the one in the picture below.

.. figure:: img/layers_uploading_page.png
     :align: center

     *The Layers Uploading page*

| Through the :guilabel:`Choose Files` button you can select files from your disk, make sure they are valid raster or vector spatial data. You can also change the default *Permissions* settings (see :ref:`layer-permissions` for further information on how to set permissions).
| Select the *charset*, then click on :guilabel:`Upload files` to start the process or click :guilabel:`Clear` to remove all the loaded files form the page.

.. figure:: img/upload_shapefile.gif
     :align: center

     *Shapefile Uploading*

In this example the ``roads`` ESRI Shapefile, with all its mandatory files (`.shp`, `.shx`, `.dbf` and `.prj`), has been chosen.
A progress bar shows the operation made during the layer upload and alerts you when the process is over.
When the process ends click the :guilabel:`Layer Info` to check the layer has been correctly uploaded.

.. note:: There are lot of free spatial dataset available in the Internet. In this example, an extract of the Berlin city center roads map from the `BBBike extracts OpenStreetMap <https://extract.bbbike.org>`_ dataset has been used.

In the next paragraphs you will learn how to create a layer from scratch, how to set permissions, how to explore the layer properties and how to edit them.
