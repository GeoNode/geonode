/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

var mapPanel;

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
    map.addControl(new OpenLayers.Control.LayerSwitcher());

    var addLayer = function() {
        var wmslayer = new OpenLayers.Layer.WMS("Bodies of Water",
            "http://demo.opengeo.org/geoserver/wms?",
            {layers: 'topp:tasmania_water_bodies', format: 'image/png', transparent: true},
            {singleTile: true});
        mapPanel.map.addLayer(wmslayer);
    };

    var removeLayer = function() {
        mapPanel.map.removeLayer(mapPanel.map.layers[1]);
    };

    var moveLayer = function(idx) {
        mapPanel.map.setLayerIndex(mapPanel.map.layers[0], idx);
    };

    var toggleVisibility = function() {
        mapPanel.map.layers[1].setVisibility(!mapPanel.map.layers[1].getVisibility());
    };

    var updateHideInLegend = function() {
        mapPanel.layers.getAt(1).set("hideInLegend", true);
    };

    var updateLegendUrl = function() {
        mapPanel.layers.getAt(0).set("legendURL", "http://www.geoext.org/trac/geoext/chrome/site/img/GeoExt.png");
    };

    var mapPanel = new GeoExt.MapPanel({
        region: 'center',
        height: 400,
        width: 600,
        map: map,
        center: new OpenLayers.LonLat(146.4, -41.6),
        zoom: 7
    });

    var legendPanel = new GeoExt.LegendPanel({
        labelCls: 'mylabel',
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
                {text: 'add', handler: addLayer},
                {text: 'remove', handler: removeLayer},
                {text: 'movetotop', handler: function() { moveLayer(10); } },
                {text: 'moveup', handler: function() { moveLayer(1); } },
                {text: 'togglevis', handler: toggleVisibility},
                {text: 'hide', handler: updateHideInLegend},
                {text: 'legendurl', handler: updateLegendUrl}
            ]
        }),
        items: [legendPanel, mapPanel]
    });
});
