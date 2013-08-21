.. _layers.upload:

Uploading a layer
=================

Now that we have taken a tour of GeoNode and viewed existing layers, the next step is to upload our own.

In your data pack is a directory called :file:`data`. Inside that directory is a shapefile called :file:`san_andres_y_providencia_administrative.shp`. This is a data set containing ... This will be the first layer that we will upload to GeoNode.

.. todo:: What does it contain?

#. Navigate to the GeoNode welcome page.

   .. todo:: Where is it located again?

#. Click the :guilabel:`Layers` link on the top toolbar. This will bring up the Layers menu.

   .. figure:: img/toolbar.png

      *Main toolbar for GeoNode*

   .. figure:: ../intro/img/layers.png

      *Layers menu*

#. Click :guilabel:`Upload Layers` in the Layers toolbar. This will bring up the upload form

   .. figure:: img/layerstoolbar.png

      *Layers toolbar*

   .. figure:: img/uploadform.png

      *Upload Layers form*

#. Fill out the form.

   * Leave the title blank for now (it will be autopopulated based on the file name).

   * Next to the :guilabel:`Data` field, click the :guilabel:`Browse...` button. This will bring up a local file dialog. Navigate to your data folder and select the :file:`san_andres_y_providencia_administrative.shp` file.

   * A few new options will appear once this shapefile is selected. Next to the :guilabel:`DBF` field, click the :guilabel:`Browse...` button. This will bring up the same local file dialog. Select the :file:`san_andres_y_providencia_administrative.dbf` file.

   * Repeat the same process for the :guilabel:`SHX` and :guilabel:`PRJ` fields.

   * Leave the rest of the fields blank.

   .. figure:: img/uploadformfilled.png

      *Files ready for upload*
      
#. GeoNode has the ability to restrict who can view, edit, and manage layers. On the right side of the page, under :guilabel:`Who can view and download this data`, select :guilabel:`Any registered user`. This will ensure that anonymous view access is disabled.

#. In the same area, under :guilabel:`Who can edit this data`, select your username. This will ensure that only you are able to edit the data in the layer.

   .. figure:: img/uploadpermissions.png

      *Permissions for new layer*

#. Click :guilabel:`Upload` to upload the data and create a layer. A dialog will display showing the progress of the upload.

   .. figure:: img/uploading.png

      *Upload in progress*

Your layer has been uploaded to GeoNode.
