/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

var mapPanel;

Ext.onReady(function() {
    var map = new OpenLayers.Map();
    var layer = new OpenLayers.Layer.WMS(
        "Global Imagery",
        "http://demo.opengeo.org/geoserver/wms",
        {layers: 'bluemarble'}
    );
    map.addLayer(layer);

    mapPanel = new GeoExt.MapPanel({
        title: "GeoExt MapPanel",
        renderTo: "mappanel",
        height: 400,
        width: 600,
        map: map,
        center: new OpenLayers.LonLat(5, 45),
        zoom: 4
    });
});

// functions for resizing the map panel
function mapSizeUp() {
    var size = mapPanel.getSize();
    size.width += 40;
    size.height += 40;
    mapPanel.setSize(size);
}
function mapSizeDown() {
    var size = mapPanel.getSize();
    size.width -= 40;
    size.height -= 40;
    mapPanel.setSize(size);
}

