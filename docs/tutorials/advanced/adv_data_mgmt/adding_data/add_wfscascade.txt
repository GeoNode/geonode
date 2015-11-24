.. module:: geoserver.add_wfscascade
   :synopsis: Learn how to add a WFS Cascade Layer.

.. _geoserver.add_wfscascade:

Adding a WFS Cascade Layer
--------------------------

GeoServer has the ability to load data from a remote Web Feature Server (WFS).
This is useful if the remote WFS lacks certain functionality that GeoServer contains.
For example, if the remote WFS is not also a Web Map Server (WMS), data from the WFS can be cascaded through GeoServer to utilize GeoServer's WMS.
If the remote WFS has a WMS but that WMS cannot output KML, data can be cascaded through GeoServer's WMS to output KML.

**Configuration**

The configuration as usage of the cascaded layers follows GeoServer traditional ease of use.

#. Open the web browser and navigate to the GeoServer `Welcome Page <http://localhost:8083/geoserver>`_.

#. Select :guilabel:`Add stores` from the interface. 

   .. figure:: img/geotiff_addstores.png

#. Select :guilabel:`Web Feature Server` from the set of available Vector Data Sources. 

#. Specify a proper name (as an instance, :file:`wfs-cascade`) in the :guilabel:`Data Source Name` field of the interface. 
#. Specify :file:`http://demo1.geo-solutions.it/geoserver-enterprise/ows?service=wfs&version=1.0.0&request=GetCapabilities` as the URL of the sample data in the :guilabel:`Capabilities URL` field. 

   .. figure:: img/wfscascade_store.png

#. Make sure that the HTTP Authentication fields match the remote server authorization you have on it (In this case the server is open so we don't need them). 

#. Click :guilabel:`Save`. 

#. Publish the layer by clicking on the :guilabel:`publish` link near the `geosolutions_country` layer name. Notice that you can also add more layers later.

   .. figure:: img/wfscascading_publish.png

#. Check the Coordinate Reference Systems and the Bounding Boxes fields are properly set and click on :guilabel:`Save`. 

   .. figure:: img/wfscascade_bbox.png

#. At this point the new WMS Layer is being published with GeoServer. You can use the layer preview to inspect the data.

   .. figure:: img/wfscascading_preview.png
