/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[legendpanel]
 *  Legend Panel
 *  ------------
 *  Display a layer legend in a panel.
 */


var mapPanel, legendPanel;

Ext.onReady(function() {
    var map = new OpenLayers.Map({allOverlays: true});
    map.addLayers([
        new OpenLayers.Layer.WMS(
            "Tasmania",
            "http://demo.opengeo.org/geoserver/wms?",
            {layers: 'topp:tasmania_state_boundaries', format: 'image/png', transparent: true},
            {singleTile: true}),
        new OpenLayers.Layer.WMS(
            "Cities and Roads",
            "http://demo.opengeo.org/geoserver/wms?",
            {layers: 'topp:tasmania_cities,topp:tasmania_roads', format: 'image/png', transparent: true},
            {singleTile: true}),
        new OpenLayers.Layer.Vector('Polygons', {styleMap: new OpenLayers.StyleMap({
                "default": new OpenLayers.Style({
                    pointRadius: 8,
                    fillColor: "#00ffee",
                    strokeColor: "#000000",
                    strokeWidth: 2
                }) }) })
    ]);
    map.layers[2].addFeatures([
        new OpenLayers.Feature.Vector(OpenLayers.Geometry.fromWKT(
            "POLYGON(146.1 -41, 146.2 -41, 146.2 -41.1, 146.1 -41.1)"))
    ]);
    map.addControl(new OpenLayers.Control.LayerSwitcher());

    var addRemoveLayer = function() {
        if(mapPanel.map.layers.indexOf(water) == -1) {
            mapPanel.map.addLayer(water);
        } else {
            mapPanel.map.removeLayer(water);
        }
    };

    var moveLayer = function(idx) {
        var layer = layerRec0.getLayer();
        var idx = mapPanel.map.layers.indexOf(layer) == 0 ?
            mapPanel.map.layers.length : 0;
        mapPanel.map.setLayerIndex(layerRec0.getLayer(), idx);
    };

    var toggleVisibility = function() {
        var layer = layerRec1.getLayer();
        layer.setVisibility(!layer.getVisibility());
    };

    var updateHideInLegend = function() {
        layerRec0.set("hideInLegend", !layerRec0.get("hideInLegend"));
    };

    var updateLegendUrl = function() {
        var url = layerRec0.get("legendURL");
        layerRec0.set("legendURL", otherUrl);
        otherUrl = url;
    };

    mapPanel = new GeoExt.MapPanel({
        region: 'center',
        height: 400,
        width: 600,
        map: map,
        center: new OpenLayers.LonLat(146.4, -41.6),
        zoom: 7
    });
    
    // give the record of the 1st layer a legendURL, which will cause
    // UrlLegend instead of WMSLegend to be used
    var layerRec0 = mapPanel.layers.getAt(0);
    layerRec0.set("legendURL", "http://demo.opengeo.org/geoserver/wms?FORMAT=image%2Fgif&TRANSPARENT=true&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetLegendGraphic&EXCEPTIONS=application%2Fvnd.ogc.se_xml&LAYER=topp%3Atasmania_state_boundaries");

    // store the layer that we will modify in toggleVis()
    var layerRec1 = mapPanel.layers.getAt(1);

    // stores another legendURL for the legendurl button action
    var otherUrl = "http://www.geoext.org/trac/geoext/chrome/site/img/GeoExt.png";

    // create another layer for the add/remove button action
    var water = new OpenLayers.Layer.WMS("Bodies of Water",
        "http://demo.opengeo.org/geoserver/wms?",
        {layers: 'topp:tasmania_water_bodies', format: 'image/png', transparent: true},
        {singleTile: true});

    legendPanel = new GeoExt.LegendPanel({
        defaults: {
            labelCls: 'mylabel',
            style: 'padding:5px'
        },
        bodyStyle: 'padding:5px',
        width: 350,
        autoScroll: true,
        region: 'west'
    });

    new Ext.Panel({
        title: "GeoExt LegendPanel Demo",
        layout: 'border',
        renderTo: 'view',
        height: 400,
        width: 800,
        tbar: new Ext.Toolbar({
            items: [
                {text: 'add/remove', handler: addRemoveLayer},
                {text: 'movetop/bottom', handler: moveLayer },
                {text: 'togglevis', handler: toggleVisibility},
                {text: 'hide/show', handler: updateHideInLegend},
                {text: 'legendurl', handler: updateLegendUrl}
            ]
        }),
        items: [legendPanel, mapPanel]
    });
});
