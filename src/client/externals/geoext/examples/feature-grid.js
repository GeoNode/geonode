/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

var mapPanel, store, gridPanel, mainPanel;

Ext.onReady(function() {
    // create map instance
    var map = new OpenLayers.Map();
    var wmsLayer = new OpenLayers.Layer.WMS(
        "vmap0",
        "http://labs.metacarta.com/wms/vmap0",
        {layers: 'basic'}
    );

    // create vector layer
    var vecLayer = new OpenLayers.Layer.Vector("vector");
    map.addLayers([wmsLayer, vecLayer]);

    // create map panel
    mapPanel = new GeoExt.MapPanel({
        title: "Map",
        region: "center",
        height: 400,
        width: 600,
        map: map,
        center: new OpenLayers.LonLat(5, 45),
        zoom: 6
    });
 
    // create feature store, binding it to the vector layer
    store = new GeoExt.data.FeatureStore({
        layer: vecLayer,
        fields: [
            {name: 'name', type: 'string'},
            {name: 'elevation', type: 'float'}
        ],
        proxy: new GeoExt.data.ProtocolProxy({
            protocol: new OpenLayers.Protocol.HTTP({
                url: "data/summits.json",
                format: new OpenLayers.Format.GeoJSON()
            })
        }),
        autoLoad: true
    });

    // create grid panel configured with feature store
    gridPanel = new Ext.grid.GridPanel({
        title: "Feature Grid",
        region: "east",
        store: store,
        width: 320,
        columns: [{
            header: "Name",
            width: 200,
            dataIndex: "name"
        }, {
            header: "Elevation",
            width: 100,
            dataIndex: "elevation"
        }],
        sm: new GeoExt.grid.FeatureSelectionModel() 
    });

    // create a panel and add the map panel and grid panel
    // inside it
    mainPanel = new Ext.Panel({
        renderTo: "mainpanel",
        layout: "border",
        height: 400,
        width: 920,
        items: [mapPanel, gridPanel]
    });
});

