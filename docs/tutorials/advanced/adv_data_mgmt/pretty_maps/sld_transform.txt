.. _geoserver.sld_transform:


Geometry transformations
========================

This section show how to GeoServer provides a number of filter functions that can actually manipulate geometries by transforming them into something different: this is what we call *geometry transformations in SLD*.

Extracting vertices
^^^^^^^^^^^^^^^^^^^

#. Using skills learned in the :ref:`adding styles <geoserver.add_style>` section, create a new style named :guilabel:`mainrd_transform` using the following SLD:
 		  
   .. code-block:: xml

    <?xml version="1.0" encoding="ISO-8859-1"?>
    <StyledLayerDescriptor version="1.0.0"
      xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc"
      xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
      <NamedLayer>
        <Name>Roads and vertices</Name>
        <UserStyle>
          <FeatureTypeStyle>
            <Rule>
              <LineSymbolizer>
                <Stroke />
              </LineSymbolizer>
              <PointSymbolizer>
                <Geometry>
                  <ogc:Function name="vertices">
                    <ogc:PropertyName>the_geom</ogc:PropertyName>
                  </ogc:Function>
                </Geometry>
                <Graphic>
                  <Mark>
                    <WellKnownName>circle</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#FF0000</CssParameter>
                    </Fill>
                  </Mark>
                  <Size>6</Size>
                </Graphic>
              </PointSymbolizer>
            </Rule>
          </FeatureTypeStyle>
        </UserStyle>
      </NamedLayer>
    </StyledLayerDescriptor>

   .. note:: The ``vertices`` function returns a multi-point made with all the vertices of the original geometry

#. Using skills learned in the :ref:`adding styles <geoserver.add_style>` section, modify the styling of the ``Mainrd`` layer and add ``mainrd_transform`` as an alternate style (hint, select the ``mainrd_transform`` style in the first list below "available styles" and then use the right arrow to move it in the "selected styles"):

.. figure:: img/tx_secondary_style.png

   Adding the mainrd_transform style as a secondary style for Mainrd

#. Use the Preview link to display the Mainrd layer, then open the options box and choose the alternate style from the drop down:
   
   .. figure:: img/sld_transform2.png

      Extracting and showing the vertices out of a geometry


Line buffer
^^^^^^^^^^^

#. Using skills learned in the geoserver.addstyle section, create a new style :guilabel:`mainrd_buffer` using the following SLD

	.. code-block:: xml

	  <?xml version="1.0" encoding="ISO-8859-1"?>
	  <StyledLayerDescriptor version="1.0.0"
	  xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc"
	  xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
		<NamedLayer>
		  <Name>Roads and vertices</Name>
		  <UserStyle>
			<FeatureTypeStyle>
			  <Rule>
				<PolygonSymbolizer>
				  <Geometry>
					<ogc:Function name="buffer">
					  <ogc:PropertyName>the_geom</ogc:PropertyName>
					  <ogc:Literal>200</ogc:Literal>
					</ogc:Function>
				  </Geometry>
				   <Fill>
					<CssParameter name="fill">#7F7F7F</CssParameter>
					<CssParameter name="fill-opacity">0.3</CssParameter>
				  </Fill>
				</PolygonSymbolizer>
				<LineSymbolizer>
				  <Stroke />
				</LineSymbolizer>
			  </Rule>
			</FeatureTypeStyle>
		  </UserStyle>
		</NamedLayer>
	  </StyledLayerDescriptor>


   .. note:: The ``buffer`` function builds a polygon of all the points that are withing the specified distance from the original geometry.

#. As done previously, modify the styling of the ``Mainrd`` layer and add ``mainrd_buffer`` as an alternate style:

.. figure:: img/tx_secondary_style_buffer.png

   Adding the mainrd_buffer style as a secondary style for Mainrd


#. Use the `Map Preview <http://localhost:8083/geoserver/mapPreview.do>`_ to preview the new style.

   .. figure:: img/sld_transform1.png

      Extracting start and end point of a line
