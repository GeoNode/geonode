var doc = (new OpenLayers.Format.XML).read(
    '<ViewContext xmlns="http://www.opengis.net/context" version="1.1.0" id="default.wmc" xsi:schemaLocation="http://www.opengis.net/context http://schemas.opengis.net/context/1.1.0/context.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' +
      '<General>' +
        '<Window width="1031" height="389"/>' +
        '<BoundingBox minx="-37179.8441128839986" miny="6691080.05881679989" maxx="540179.844112879946" maxy="6908919.94118320011" SRS="EPSG:2154"/>' +
        '<Title/>' +
        '<Extension>' +
          '<ol:maxExtent xmlns:ol="http://openlayers.org/context" minx="83000.0000000000000" miny="6700000.00000000000" maxx="420000.000000000000" maxy="6900000.00000000000"/>' +
        '</Extension>' +
      '</General>' +
      '<LayerList>' +
        '<Layer queryable="0" hidden="0">' +
          '<Server service="OGC:WMS" version="1.1.1">' +
            '<OnlineResource xlink:type="simple" xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="../geoserver/gwc/service/wms"/>' +
          '</Server>' +
          '<Name>geob:SC1000_0050_7130_L93</Name>' +
          '<Title>Scan 1000</Title>' +
          '<Abstract>Scan 1000 abstract</Abstract>' +
          '<sld:MinScaleDenominator xmlns:sld="http://www.opengis.net/sld">250000.0000000000</sld:MinScaleDenominator>' +
          '<sld:MaxScaleDenominator xmlns:sld="http://www.opengis.net/sld">2000000.000000000</sld:MaxScaleDenominator>' +
          '<FormatList>' +
            '<Format current="1">image/png</Format>' +
          '</FormatList>' +
          '<StyleList>' +
            '<Style>' +
              '<Name/>' +
              '<Title/>' +
            '</Style>' +
          '</StyleList>' +
          '<Extension>' +
            '<ol:maxExtent xmlns:ol="http://openlayers.org/context" minx="83000.0000000000000" miny="6700000.00000000000" maxx="420000.000000000000" maxy="6900000.00000000000"/>' +
            '<ol:numZoomLevels xmlns:ol="http://openlayers.org/context">4</ol:numZoomLevels>' +
            '<ol:units xmlns:ol="http://openlayers.org/context">m</ol:units>' +
            '<ol:isBaseLayer xmlns:ol="http://openlayers.org/context">false</ol:isBaseLayer>' +
            '<ol:opacity xmlns:ol="http://openlayers.org/context">1</ol:opacity>' +
            '<ol:displayInLayerSwitcher xmlns:ol="http://openlayers.org/context">true</ol:displayInLayerSwitcher>' +
            '<ol:singleTile xmlns:ol="http://openlayers.org/context">false</ol:singleTile>' +
          '</Extension>' +
        '</Layer>' +
        '<Layer queryable="1" hidden="0">' +
          '<Server service="OGC:WMS" version="1.1.1">' +
            '<OnlineResource xlink:type="simple" xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="../geoserver/wms?SERVICE=WMS&amp;"/>' +
          '</Server>' +
          '<Name>geob:communes_geofla</Name>' +
          '<Title>Communes</Title>' +
          '<Abstract>Communes abstract</Abstract>' +
          '<FormatList>' +
            '<Format current="1">image/png</Format>' +
            '<Format>application/atom xml</Format>' +
            '<Format>application/atom+xml</Format>' +
            '<Format>application/openlayers</Format>' +
            '<Format>application/pdf</Format>' +
            '<Format>application/rss xml</Format>' +
            '<Format>application/rss+xml</Format>' +
            '<Format>application/vnd.google-earth.kml</Format>' +
            '<Format>application/vnd.google-earth.kml xml</Format>' +
            '<Format>application/vnd.google-earth.kml+xml</Format>' +
            '<Format>application/vnd.google-earth.kmz</Format>' +
            '<Format>application/vnd.google-earth.kmz xml</Format>' +
            '<Format>application/vnd.google-earth.kmz+xml</Format>' +
            '<Format>atom</Format>' +
            '<Format>image/geotiff</Format>' +
            '<Format>image/geotiff8</Format>' +
            '<Format>image/gif</Format>' +
            '<Format>image/jpeg</Format>' +
            '<Format>image/png8</Format>' +
            '<Format>image/svg</Format>' +
            '<Format>image/svg xml</Format>' +
            '<Format>image/svg+xml</Format>' +
            '<Format>image/tiff</Format>' +
            '<Format>image/tiff8</Format>' +
            '<Format>kml</Format>' +
            '<Format>kmz</Format>' +
            '<Format>openlayers</Format>' +
            '<Format>rss</Format>' +
          '</FormatList>' +
          '<StyleList>' +
            '<Style>' +
              '<Name>line</Name>' +
              '<Title>1 px blue line</Title>' +
              '<Abstract>Default line style, 1 pixel wide blue</Abstract>' +
            '</Style>' +
            '<Style>' +
              '<Name>dpt_classif</Name>' +
              '<Title>Classification par départements</Title>' +
            '</Style>' +
          '</StyleList>' +
          '<Extension>' +
            '<ol:maxExtent xmlns:ol="http://openlayers.org/context" minx="83000.0000000000000" miny="6700000.00000000000" maxx="420000.000000000000" maxy="6900000.00000000000"/>' +
            '<ol:transparent xmlns:ol="http://openlayers.org/context">true</ol:transparent>' +
            '<ol:numZoomLevels xmlns:ol="http://openlayers.org/context">13</ol:numZoomLevels>' +
            '<ol:units xmlns:ol="http://openlayers.org/context">m</ol:units>' +
            '<ol:isBaseLayer xmlns:ol="http://openlayers.org/context">false</ol:isBaseLayer>' +
            '<ol:opacity xmlns:ol="http://openlayers.org/context">0.5</ol:opacity>' +
            '<ol:displayInLayerSwitcher xmlns:ol="http://openlayers.org/context">true</ol:displayInLayerSwitcher>' +
            '<ol:singleTile xmlns:ol="http://openlayers.org/context">true</ol:singleTile>' +
          '</Extension>' +
        '</Layer>' +
        '<Layer queryable="1" hidden="0">' +
          '<Server service="OGC:WMS" version="1.1.1">' +
            '<OnlineResource xlink:type="simple" xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="http://geolittoral.application.equipement.gouv.fr/map/mapserv?map=/opt/data/carto/applis/geolittoral/map/metropole.www.map&amp;"/>' +
          '</Server>' +
          '<Name>Sentiers_littoraux</Name>' +
          '<Title>Sentiers littoraux</Title>' +
          '<FormatList>' +
            '<Format current="1">image/png</Format>' +
            '<Format>image/gif</Format>' +
            '<Format>image/png; mode=24bit</Format>' +
            '<Format>image/jpeg</Format>' +
            '<Format>image/vnd.wap.wbmp</Format>' +
            '<Format>image/tiff</Format>' +
            '<Format>image/svg+xml</Format>' +
          '</FormatList>' +
          '<StyleList>' +
            '<Style>' +
              '<Name>default</Name>' +
              '<Title>default</Title>' +
            '</Style>' +
          '</StyleList>' +
          '<Extension>' +
            '<ol:maxExtent xmlns:ol="http://openlayers.org/context" minx="83000.0000000000000" miny="6700000.00000000000" maxx="420000.000000000000" maxy="6900000.00000000000"/>' +
            '<ol:transparent xmlns:ol="http://openlayers.org/context">true</ol:transparent>' +
            '<ol:numZoomLevels xmlns:ol="http://openlayers.org/context">13</ol:numZoomLevels>' +
            '<ol:units xmlns:ol="http://openlayers.org/context">m</ol:units>' +
            '<ol:isBaseLayer xmlns:ol="http://openlayers.org/context">false</ol:isBaseLayer>' +
            '<ol:opacity xmlns:ol="http://openlayers.org/context">1</ol:opacity>' +
            '<ol:displayInLayerSwitcher xmlns:ol="http://openlayers.org/context">true</ol:displayInLayerSwitcher>' +
            '<ol:singleTile xmlns:ol="http://openlayers.org/context">true</ol:singleTile>' +
          '</Extension>' +
        '</Layer>' +
      '</LayerList>' +
    '</ViewContext>'
);
