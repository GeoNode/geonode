/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 *
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[permalink]
 *  Permalink
 *  ---------
 *  Display a permalink each time the map changes position.
 */

var permalinkProvider;

Ext.onReady(function() {

    // set a permalink provider
    permalinkProvider = new GeoExt.state.PermalinkProvider({encodeType: false});
    Ext.state.Manager.setProvider(permalinkProvider);

    var map = new OpenLayers.Map();
    map.addLayers([
        new OpenLayers.Layer.WMS(
            "Imagery",
            "http://maps.opengeo.org/geowebcache/service/wms",
            {layers: "bluemarble"}
        ),
        new OpenLayers.Layer.WMS(
            "OSM",
            "http://maps.opengeo.org/geowebcache/service/wms",
            {layers: "openstreetmap"}
        )
    ]);
    map.addControl(new OpenLayers.Control.LayerSwitcher());

    var mapPanel = new GeoExt.MapPanel({
        title: "GeoExt MapPanel",
        renderTo: "mappanel",
        height: 400,
        width: 600,
        map: map,
        center: new OpenLayers.LonLat(5, 45),
        zoom: 4,
        stateId: "map",
        prettyStateKeys: true
    });

    // update link when state chnages
    var onStatechange = function(provider) {
        var l = provider.getLink();
        Ext.get("permalink").update("<a href=" + l + ">" + l + "</a>");
    };
    permalinkProvider.on({statechange: onStatechange});
});
