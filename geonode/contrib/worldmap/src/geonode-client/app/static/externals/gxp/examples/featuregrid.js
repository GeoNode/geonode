/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

var store, map, grid;
Ext.onReady(function() {
    
    // create a new attributes store
    store = new GeoExt.data.FeatureStore({
        fields: [
            {name: 'the_geom'},
            {name: 'STATE_NAME', type: 'string'},
            {name: 'STATE_FIPS', type: 'string'},
            {name: 'SUB_REGION', type: 'string'},
            {name: 'STATE_ABBR', type: 'string'},
            {name: 'LAND_KM', type: 'float'}
        ],
        proxy: new GeoExt.data.ProtocolProxy({
            protocol: new OpenLayers.Protocol.HTTP({
                url: "data/getfeature.xml",
                format: new OpenLayers.Format.GML({
                    featureNS: "http://www.openplans.org/topp"
                })
            })
        }),
        autoLoad: true
    });
    
    // creates the map that will contain the vector layer with features
    map = new OpenLayers.Map("map", {theme: null});
    map.addLayer(new OpenLayers.Layer.WMS(
        "Global Imagery",
        "http://demo.opengeo.org/geoserver/wms",
        {layers: 'bluemarble'}
    ));
    map.setCenter(new OpenLayers.LonLat(-100, 35), 3);

    // create a grid to display records from the store
    grid = new gxp.grid.FeatureGrid({
        title: "Feature Attributes",
        store: store,
        ignoreFields: ["the_geom"],
        map: map,
        renderTo: "grid",
        height: 300,
        width: 350
    });    

});
