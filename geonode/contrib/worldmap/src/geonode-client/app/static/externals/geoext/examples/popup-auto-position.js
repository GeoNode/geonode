/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 *
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[popup]
 *  Feature Popup
 *  -------------
 *  Display a popup with feature information, which is positioned automatically.
 */

var mapPanel, popup;

Ext.onReady(function() {

    // create a vector layer, add features into it
    var vectorLayer = new OpenLayers.Layer.Vector("vector");
    vectorLayer.addFeatures([
        new OpenLayers.Feature.Vector(
            new OpenLayers.Geometry.Point(-75, 45)
        ), new OpenLayers.Feature.Vector(
            new OpenLayers.Geometry.Point(+75, -45)
        ), new OpenLayers.Feature.Vector(
            new OpenLayers.Geometry.Point(+75, +45)
        ), new OpenLayers.Feature.Vector(
            new OpenLayers.Geometry.Point(-75, -45)
        )]

    );

    // create select feature control
    var selectCtrl = new OpenLayers.Control.SelectFeature(vectorLayer);

    // define "createPopup" function
    var bogusMarkup = "Lorem ipsum dolor sit amet, consectetuer adipiscing elit.";
    function createPopup(feature) {
        popup = new GeoExt.Popup({
            title: 'My Popup',
            location: feature,
            width:200,
            html: bogusMarkup,
            maximizable: true,
            collapsible: true,
            anchorPosition: "auto"
        });
        // unselect feature when the popup
        // is closed
        popup.on({
            close: function() {
                if(OpenLayers.Util.indexOf(vectorLayer.selectedFeatures,
                                           this.feature) > -1) {
                    selectCtrl.unselect(this.feature);
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
            layers: [
                new OpenLayers.Layer.WMS(
                    "OpenLayers WMS",
                    "http://vmap0.tiles.osgeo.org/wms/vmap0",
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
