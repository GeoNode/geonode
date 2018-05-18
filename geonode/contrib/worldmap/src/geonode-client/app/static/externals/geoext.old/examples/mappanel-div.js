/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[mappanel-div]
 *  Map Panel
 *  ---------
 *  Render a map panel in any block level page element.
 */

var mapPanel;

Ext.onReady(function() {
    Ext.state.Manager.setProvider(new Ext.state.CookieProvider());
    var map = new OpenLayers.Map();
    var layer = new OpenLayers.Layer.WMS(
        "Global Imagery",
        "http://maps.opengeo.org/geowebcache/service/wms",
        {layers: "bluemarble"}
    );
    map.addLayer(layer);

    mapPanel = new GeoExt.MapPanel({
        title: "GeoExt MapPanel",
        renderTo: "mappanel",
        stateId: "mappanel",
        height: 400,
        width: 600,
        map: map,
        center: new OpenLayers.LonLat(5, 45),
        zoom: 4,
        // getState and applyState are overloaded so panel size
        // can be stored and restored
        getState: function() {
            var state = GeoExt.MapPanel.prototype.getState.apply(this);
            state.width = this.getSize().width;
            state.height = this.getSize().height;
            return state;
        },
        applyState: function(state) {
            GeoExt.MapPanel.prototype.applyState.apply(this, arguments);
            this.width = state.width;
            this.height = state.height;
        }
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

