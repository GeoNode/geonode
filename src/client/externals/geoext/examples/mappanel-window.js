/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

var mapPanel;

Ext.onReady(function() {
    new Ext.Window({
        title: "GeoExt MapPanel Window",
        height: 400,
        width: 600,
        layout: "fit",
        items: [{
            xtype: "gx_mappanel",
            id: "mappanel",
            layers: [new OpenLayers.Layer.WMS(
                "Global Imagery",
                "http://demo.opengeo.org/geoserver/wms",
                {layers: 'bluemarble'}
            )],
            extent: "-5,35,15,55"
        }]
    }).show();
    
    mapPanel = Ext.getCmp("mappanel");
});
