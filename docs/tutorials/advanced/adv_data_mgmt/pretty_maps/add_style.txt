.. module:: geoserver.add_style

.. _geoserver.add_style:


Adding a Style
--------------

The most important function of a web map server is the ability to style and render data. This section covers the task of adding a new style to GeoServer and configuring the default style for a particular layer.

#. From the GeoServer `Welcome Page <http://localhost:8083/geoserver>`_ navigate to :guilabel:`Style`.

   .. figure:: img/style1.png

      Navigating to Style configuration
     
#. Click :guilabel:`New`

   .. figure:: img/style2.png

     Adding a new style

#. Enter "mainrd" in the :guilabel:`Name` field and notice the file upload dialogue :guilabel:`SLD file`.

   .. figure:: img/style3.png

      Specifying style name and populating from a file.

#. Navigate to the workshop (on Linux) :file:`${TRAINING_ROOT}/data/user_data/` directory (on Windows :file:`%TRAINING_ROOT%\\data\\user_data\\`), select the :file:`foss4g_mainrd.sld` file, and click :guilabel:`Upload`.


   .. note:: In GeoServer, styles are represented via SLD (Styled Layer Descriptor) documents. SLD is an XML format for specifying the symbolization of a layer. When an SLD document is uploaded the contents are shown in the text editor.  The editor can be used to edit the contents of the SLD directly.

#. Add the new style by clicking :guilabel:`Submit`. Once it's save, you should see something like this:

   .. figure:: img/style4.png

      Submitting style

#. After having created the style, it's time to apply it to a vector layer. Click on the :guilabel:`Layers` link.

   .. figure:: img/style5.png

      Navigating to Layers
     
#. Select the "Mainrd" on the `Layers` page.

   .. figure:: img/style6.png

      Selecting a layer

#. Select the :guilabel:`Publish` tab.

   .. figure:: img/style7.png

      Publish tab

#. Assign the new created style "mainrd" as the default style.


   .. figure:: img/style8.png

      Publish tab

   .. warning:: Many new users mistake the :guilabel:`Available Styles` for the :guilabel:`Default Style`, please take into account that they are different, the default one allows that style to be used implicitly when no style is specified in a map request, while the available ones are just optional compatible styles.

   .. note:: Geoserver 2.x assigns a default style depending on the geometry of the objects and the type, for example: `line`, `poly`, `raster`, `point`.

#. Scroll to the bottom of the page and hit :guilabel:`Save`.

#. Use the map preview to show how the style, please note you'll have to zoom in once to show the data due to the map scale filters (``MaxScaleDenominator`` directive in the SLD).
