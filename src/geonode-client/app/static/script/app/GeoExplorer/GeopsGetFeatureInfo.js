/* Copyright (c) 2006-2012 by OpenLayers Contributors (see authors.txt for
 * full list of contributors). Published under the 2-clause BSD license.
 * See license.txt in the OpenLayers distribution or repository for the
 * full text of the license. */


/**
 * requires OpenLayers/Control.js
 * requires OpenLayers/Handler/Click.js
 * requires OpenLayers/Handler/Hover.js
 * requires OpenLayers/Request.js
 * requires OpenLayers/Format/WMSGetFeatureInfo.js
 */

/**
 * Class: OpenLayers.Control.WMSGetFeatureInfo
 * The WMSGetFeatureInfo control uses a WMS query to get information about a point on the map.  The
 * information may be in a display-friendly format such as HTML, or a machine-friendly format such
 * as GML, depending on the server's capabilities and the client's configuration.  This control
 * handles click or hover events, attempts to parse the results using an OpenLayers.Format, and
 * fires a 'getfeatureinfo' event with the click position, the raw body of the response, and an
 * array of features if it successfully read the response.
 *
 * Inherits from:
 *  - <OpenLayers.Control>
 */
GeoExplorer.GeopsGetFeatureInfo = OpenLayers.Class(OpenLayers.Control.WMSGetFeatureInfo, {


    /**
     * Property: infoFormat
     * {String} The mimetype to request from the server. If you are using
     * drillDown mode and have multiple servers that do not share a common
     * infoFormat, you can override the control's infoFormat by providing an
     * INFO_FORMAT parameter in your <OpenLayers.Layer.WMS> instance(s).
     */
    infoFormat: 'text/json',


    /**
     * Property: format
     * {<OpenLayers.Format>} A format for parsing GetFeatureInfo responses.
     *     Default is <OpenLayers.Format.JSON>.
     */
    format: null,


    radius: 10,

    /**
    /**
     * Method: buildWMSOptions
     * Build an object with the relevant WMS options for the GetFeatureInfo request
     *
     * Parameters:
     * url - {String} The url to be used for sending the request
     * layers - {Array(<OpenLayers.Layer.WMS)} An array of layers
     * clickPosition - {<OpenLayers.Pixel>} The position on the map where the mouse
     *     event occurred.
     * format - {String} The format from the corresponding GetMap request
     */
    buildWMSOptions: function(url, layers, clickPosition, format) {
        var layerNames = [], styleNames = [];
        for (var i = 0, len = layers.length; i < len; i++) {
            if (layers[i].params.LAYERS != null) {
                layerNames = layerNames.concat(layers[i].params.LAYERS);
                styleNames = styleNames.concat(this.getStyleNames(layers[i]));
            }
        }
        var firstLayer = layers[0];
        // use the firstLayer's projection if it matches the map projection -
        // this assumes that all layers will be available in this projection
        var projection = this.map.getProjection();
        var layerProj = new OpenLayers.Projection("EPSG:4326");
        if (layerProj && layerProj.equals(this.map.getProjectionObject())) {
            projection = layerProj.getCode();
        }

        var pixelTolerance = 5; // for getFeatureInfo - will get all points within roughly 5 pixels regardless of zoom
        var mapRes = this.map.resolution * pixelTolerance;
        var boundingCircSq = mapRes*mapRes + mapRes*mapRes;
        
        
        var lonlat = this.map.getLonLatFromViewPortPx(clickPosition);
        var distString = "orddist(point(goog_x,goog_y), point(" + lonlat.lon + "," + lonlat.lat + "))"
        var SQL =  (firstLayer.params["SQL"] + " AND  " + distString + " < " + boundingCircSq +
            " order by " + distString +
            " LIMIT " + this.maxFeatures).toLowerCase();


        var params = OpenLayers.Util.extend({
                service: "WMS",
                version: firstLayer.params.VERSION,
                //SQL: firstLayer.params.SQL.replace(/select .* from/i, "SELECT * FROM "),
                SQL: SQL,
                request: "GetFeatureInfo",
                exceptions: firstLayer.params.EXCEPTIONS,
                bbox: this.map.getExtent().toBBOX(null,
                    firstLayer.reverseAxisOrder()),
                feature_count: this.maxFeatures,
                height: this.map.getSize().h,
                width: this.map.getSize().w,
                format: format,
                COLUMNS: "all",
                info_format: firstLayer.params.INFO_FORMAT || this.infoFormat
            }, (parseFloat(firstLayer.params.VERSION) >= 1.3) ?
        {
            crs: projection,
            i: parseInt(clickPosition.x),
            j: parseInt(clickPosition.y)
        } :
        {
            srs: projection,
            x: parseInt(clickPosition.x),
            y: parseInt(clickPosition.y)
        }
        );
        if (layerNames.length != 0) {
            params = OpenLayers.Util.extend({
                layers: layerNames,
                query_layers: layerNames,
                styles: styleNames
            }, params);
        }
        OpenLayers.Util.applyDefaults(params, this.vendorParams);
        return {
            url: url,
            params: OpenLayers.Util.upperCaseObject(params),
            callback: function(request) {
                this.handleResponse(clickPosition, request, url);
            },
            scope: this
        };
    },


    CLASS_NAME: "GeoExplorer.GeopsGetFeatureInfo"
});