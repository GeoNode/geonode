.. _geoserver.mosaic:

Adding an Image Mosaic to GeoServer
-----------------------------------

This section covers the task of adding and publishing a ImageMosaic file with GeoServer.

#. Navigate to the GeoServer `Welcome Page <http://localhost:8083/geoserver/web/>`_.

#. On the Welcome page locate the :guilabel:`Login` form located at the top right corner, and enter the username "admin" and password "Geos".

   .. figure:: img/vector1bis.png
      :width: 600

      GeoServer Login

#. Click the :guilabel:`Add stores` link.

   .. figure:: img/vector2bis.png

      Add stores link

#. Select the :guilabel:`ImageMosaic` link and click it.

   .. figure:: img/raster1.png

      Add a new Image Mosaic

#. On the :guilabel:`Add Raster Data Source` page enter :file:`${TRAINING_ROOT}/data/user_data/aerial` (on Windows :file:`%TRAINING_ROOT%\\data\\user_data\\aerial\\`) in the :guilabel:`URL` field (or browse the filesystem clicking on :guilabel:`Browse`), "boulder_bg" in the :guilabel:`Data Source Name` and :guilabel:`Description` fields, and click :guilabel:`Save`.

   .. figure:: img/raster2.png

      Specifying store parameters

#. After saving, you will be taken to a page that lists all the layers in the store and gives you the option to publish any of them. Click :guilabel:`Publish`.

   .. figure:: img/raster3.png

      Publishing a layer from the store

#. The :guilabel:`Coordinate Reference Systems` should be automatically populated, as well as the :guilabel:`Name`, :guilabel:`Title` and :guilabel:`Bounding Boxes` fields.

   .. note:: Change the :guilabel:`Name` and :guilabel:`Title` into **boulder_bg** as shown in the figure.
      
	The CRS and BBox fields are auto-filled with information taken from the underlying files. The coverage options section is filled with default parameters (which will be discussed later on in the training).
	
   .. figure:: img/raster5.png
   
   .. figure:: img/raster5b.png
	
		The coverage layer gui for the boulder_bg layer.
   
   .. figure:: img/raster5bis.png  
		:width: 800
		
		The coverage bands details
	  
#. Scroll to the bottom of the page and then click :guilabel:`Save`. If all went well you should see something like this:

   .. figure:: img/raster6.png

      After a successful save.

#. In the :guilabel:`Layer Preview` section click on the OpenLayers link to preview the layer in an interactive viewer, filtering by `boulder_bg` name:

   .. figure:: img/raster7.png

      Mosaic preview.


