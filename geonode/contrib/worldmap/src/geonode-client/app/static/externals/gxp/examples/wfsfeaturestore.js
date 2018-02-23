/**
 * Copyright (c) 2008-2011 The Open Planning Project
 */

// make the references to the map panel and the popup 
// global, this is useful for looking at their states
// from the console
var mapPanel, popup;

Ext.onReady(function() {

    var vectorLayer = new OpenLayers.Layer.Vector("vector");
    
    var featureStore = new gxp.data.WFSFeatureStore({
        layer: vectorLayer,
        autoLoad: true,
        url: "/geoserver/wfs",
        featureType: "cities",
        featureNS: "http://world.opengeo.org",
        schema: "/geoserver/wfs?service=WFS&request=DescribeFeatureType&version=1.1.0&typeName=world:cities",
        geometryName: "the_geom",
        fields: [
        {
            name: "City", type: "string"
        }, {
            name: "Country", type: "string"
        }]
    });

    // create select feature control
    var selectCtrl = new OpenLayers.Control.SelectFeature(vectorLayer, {clickout: false});

    // define "createPopup" function
    function createPopup(feature) {
        popup = new gxp.FeatureEditPopup({
            feature: feature,
            width: 180,
            height: 180,
            collapsible: true,
            featureStore: featureStore,
            listeners: {
                close: function() {
                    // unselect feature when the popup is closed
                    if(vectorLayer.selectedFeatures.indexOf(this.feature) > -1) {
                        selectCtrl.unselect(this.feature);
                    }
                },
                featuremodified: function(pop, feature) {
                    featureStore.save();
                }
            }
        });
        popup.show();
    }

    // create popup on "featureselected"
    vectorLayer.events.on({
        featureselected: function(e) {
            createPopup(e.feature);
        }
    });

    mapPanel = new GeoExt.MapPanel({
        title: "Map",
        renderTo: "container",
        width: 650,
        height: 356,
        map: {theme: null},
        layers: [
            new OpenLayers.Layer.WMS( 
                "OpenLayers WMS",
                "http://labs.metacarta.com/wms/vmap0",
                {layers: 'basic'} ),
            vectorLayer
        ],
        center: [25.5, 64],
        zoom: 5
    });

    mapPanel.map.addControl(selectCtrl);
    selectCtrl.activate();
});
