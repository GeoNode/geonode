/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

var mapPanel;

Ext.onReady(function() {

    // if true a google layer is used, if false
    // the bluemarble WMS layer is used
    var google = false;

    var options, layer;
    var extent = new OpenLayers.Bounds(-5, 35, 15, 55);

    if (google) {

        options = {
            projection: new OpenLayers.Projection("EPSG:900913"),
            units: "m",
            numZoomLevels: 18,
            maxResolution: 156543.0339,
            maxExtent: new OpenLayers.Bounds(-20037508, -20037508,
                                             20037508, 20037508.34)
        };

        layer = new OpenLayers.Layer.Google(
            "Google Satellite",
            {type: G_SATELLITE_MAP, sphericalMercator: true}
        );

        extent.transform(
            new OpenLayers.Projection("EPSG:4326"), options.projection
        );

    } else {
        layer = new OpenLayers.Layer.WMS(
            "Global Imagery",
            "http://demo.opengeo.org/geoserver/wms",
            {layers: 'bluemarble'},
            {isBaseLayer: true}
        );
    }

    var map = new OpenLayers.Map(options);

    new Ext.Viewport({
        layout: "border",
        items: [{
            region: "north",
            contentEl: "title",
            height: 50
        }, {
            region: "center",
            id: "mappanel",
            title: "Map",
            xtype: "gx_mappanel",
            map: map,
            layers: [layer],
            extent: extent,
            split: true
        }, {
            region: "east",
            title: "Description",
            contentEl: "description",
            width: 200,
            split: true
        }]
    });

    mapPanel = Ext.getCmp("mappanel");
});
