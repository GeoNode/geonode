.. _geoserver.filtering:


Filtering Maps
--------------


This section shows the GeoServer WMS filtering capabilities.

#. Navigate to the GeoServer `Welcome Page <http://localhost:8083/geoserver/web/>`_.

#. Go to the :guilabel:`Layer Preview` link at the bottom of the left-hand menu and show the :guilabel:`geosolutions:WorldCountries` layer with OpenLayers 'Common Format'.

   .. figure:: img/filtering1.png
      
	  Showing the GeoServer layer preview

   .. figure:: img/filtering2.png

      Show the layer with OpenLayers

#. From the :guilabel:`Filter` combo box select 'CQL' and enter the following command in the text field::

	POP_EST <= 5000000 AND POP_EST >100000

#. Click 'Apply Filter' button on the right.

   .. figure:: img/filtering3.png

      Result of the CQL filter
 
   The corresponding WMS request is::
   
	     http://localhost:8083/geoserver/geosolutions/wms?service=WMS&version=1.1.0&request=GetMap&layers=geosolutions:WorldCountries&styles=&bbox=-180.0,-89.99889902136009,180.00000000000003,83.59960032829278&width=684&height=330&srs=EPSG:4326&format=image/png&CQL_FILTER=POP_EST%20%3C=%205000000%20AND%20POP_EST%20%3E100000

#. Now enter the following command in the text field::

	DISJOINT(the_geom, POLYGON((-90 40, -90 45, -60 45, -60 40, -90 40))) AND strToLowerCase(NAME) LIKE '%on%'
	
#. Click 'Apply Filter' button on the right.

   .. figure:: img/filtering6.png

      Result of the CQL filter
 
   The corresponding WMS request is:: 
   
         http://localhost:8083/geoserver/geosolutions/wms?service=WMS&version=1.1.0&request=GetMap&layers=geosolutions:WorldCountries&styles=&bbox=-180.0,-89.99889902136009,180.00000000000003,83.59960032829278&width=684&height=330&srs=EPSG:4326&format=image/png&CQL_FILTER=DISJOINT%28the_geom%2C%20POLYGON%28%28-90%2040%2C%20-90%2045%2C%20-60%2045%2C%20-60%2040%2C%20-90%2040%29%29%29%20AND%20strToLowerCase%28NAME%29%20LIKE%20%27%25on%25%27		 

#. From the :guilabel:`Filter` combo box select 'OGC' and enter the following filter in the text field:

   .. code-block:: xml

	<Filter><PropertyIsEqualTo><PropertyName>TYPE</PropertyName><Literal>Sovereign country</Literal></PropertyIsEqualTo></Filter>

#. Click 'Apply Filter' button on the right.

   .. figure:: img/filtering4.png

      Result of the OGC filter

   The corresponding WMS request is ::
	
	     http://localhost:8083/geoserver/geosolutions/wms?service=WMS&version=1.1.0&request=GetMap&layers=geosolutions:WorldCountries&styles=&bbox=-180.0,-89.99889902136009,180.00000000000003,83.59960032829278&width=684&height=330&srs=EPSG:4326&format=image/png&CQL_FILTER=TYPE%20%3D%20%27Sovereign%20country%27
         
#. From the :guilabel:`Filter` combo box select 'FeatureID' and enter the following features ids in the text field separated by comma::

	WorldCountries.227,WorldCountries.184,WorldCountries.33

#. Click 'Apply Filter' button on the right.

   .. figure:: img/filtering5.png

      Result of the FeatureID filter

   The corresponding WMS request is::

         http://localhost:8083/geoserver/geosolutions/wms?service=WMS&version=1.1.0&request=GetMap&layers=geosolutions:WorldCountries&styles=&bbox=-180.0,-89.99889902136009,180.00000000000003,83.59960032829278&width=684&height=330&srs=EPSG:4326&format=image/png&FEATUREID=WorldCountries.227,WorldCountries.184,WorldCountries.33