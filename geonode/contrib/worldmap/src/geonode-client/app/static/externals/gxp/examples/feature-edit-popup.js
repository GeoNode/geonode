/**
 * Copyright (c) 2008-2011 The Open Planning Project
 */

// make the references to the map panel and the popup 
// global, this is useful for looking at their states
// from the console
var mapPanel, popup;

Ext.onReady(function() {

    // create a vector layer, add a feature into it
    var vectorLayer = new OpenLayers.Layer.Vector("vector");
    vectorLayer.addFeatures(
        new OpenLayers.Feature.Vector(
            new OpenLayers.Geometry.Point(-45, 5), {
                "foo": "bar", "altitude": 500, "startdate": "2012-01-06"}
        )
    );

    // create select feature control
    var selectCtrl = new OpenLayers.Control.SelectFeature(vectorLayer, {clickout: false});

    var schema = new GeoExt.data.AttributeStore({
        data: [{name: "foo", type: "xsd:string"}, {name: "altitude", type: "xsd:int"}, {name: "startdate", type: "xsd:date"}]
    });

    // define "createPopup" function
    function createPopup(feature) {
        popup = new gxp.FeatureEditPopup({
            editorPluginConfig: {ptype: "gxp_editorform", labelWidth: 50, defaults: {width: 100}, bodyStyle: "padding: 5px 5px 0"},
            feature: feature,
            schema: schema,
            width: 200,
            height: 150,
            collapsible: true,
            listeners: {
                close: function(){
                    // unselect feature when the popup is closed
                    if(vectorLayer.selectedFeatures.indexOf(this.feature) > -1) {
                        selectCtrl.unselect(this.feature);
                    }
                },
                featuremodified: function() {
                    alert("You have modified the feature.");
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

    // create Ext window including a map panel
    var mapwin = new Ext.Window({
        layout: "fit",
        title: "Map",
        closeAction: "hide",
        width: 650,
        height: 356,
        x: 50,
        y: 100,
        items: {
            xtype: "gx_mappanel",
            region: "center",
            map: {theme: null},
            layers: [
                new OpenLayers.Layer.WMS( 
                    "OpenLayers WMS",
                    "http://labs.metacarta.com/wms/vmap0",
                    {layers: 'basic'} ),
                vectorLayer
            ]
        }
    });
    mapwin.show();

    mapPanel = mapwin.items.get(0);
    mapPanel.map.addControl(selectCtrl);
    selectCtrl.activate();
});
