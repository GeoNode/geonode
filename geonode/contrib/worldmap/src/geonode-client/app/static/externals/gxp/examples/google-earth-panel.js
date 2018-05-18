/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

var map, googleEarthPanel, mapPanel;
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
        height: 400,
        width: 600,
        map: map,
        center: new OpenLayers.LonLat(5, 45),
        zoom: 4
    });


    
    // creates the map that will contain the vector layer with features
    map = new OpenLayers.Map("map", {theme: null});
    map.addLayer(new OpenLayers.Layer.WMS(
        "Global Imagery",
        "http://demo.opengeo.org/geoserver/wms",
        {layers: 'bluemarble'}
    ));
    map.setCenter(new OpenLayers.LonLat(-100, 35), 3);

        
    googleEarthPanel = new gxp.GoogleEarthPanel({
        mapPanel: mapPanel
    });

    mapPanelContainer = new Ext.Panel({
        layout: "card", 
        region: "center",
        renderTo: "container",
        width: 600,
        height: 400,
        defaults: {
            // applied to each contained panel
            border:false
        },
        items: [
            mapPanel,
            googleEarthPanel
        ],
        activeItem: 0,
        tbar: [
            new Ext.Button({
                text: "Enable 3D",
                enableToggle: true,
                toggleHandler: function(button, state){
                    if (state === true){
                        mapPanelContainer.getLayout().setActiveItem(1);
                    } else {
                        mapPanelContainer.getLayout().setActiveItem(0);
                    }
                }
            })
        ],
        scope: this
    });

});
