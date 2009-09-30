/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

var panel1, panel2, wms, slider;

Ext.onReady(function() {
    
    wms = new OpenLayers.Layer.WMS(
        "Global Imagery",
        "http://demo.opengeo.org/geoserver/wms",
        {layers: 'bluemarble'}
    );

    // create a map panel with an embedded slider
    panel1 = new GeoExt.MapPanel({
        title: "Map 1",
        renderTo: "map1-container",
        height: 300,
        width: 400,
        map: {
            controls: [new OpenLayers.Control.Navigation()]
        },
        layers: [wms],
        extent: [-5, 35, 15, 55],
        items: [{
            xtype: "gx_opacityslider",
            layer: wms,
            vertical: true,
            height: 120,
            x: 10,
            y: 10,
            plugins: new GeoExt.LayerOpacitySliderTip()
        }]
    });
    // create a separate slider bound to the map but displayed elsewhere
    slider = new GeoExt.LayerOpacitySlider({
        layer: wms,
        aggressive: true, 
        width: 200,
        isFormField: true,
        fieldLabel: "opacity",
        renderTo: "slider"
    });
        
    var clone = wms.clone();
    var wms2 = new OpenLayers.Layer.WMS(
        "OpenLayers WMS",
        "http://labs.metacarta.com/wms/vmap0",
        {layers: 'basic'}
    );
    panel2 = new GeoExt.MapPanel({
        title: "Map 2",
        renderTo: "map2-container",
        height: 300,
        width: 400,
        map: {
            controls: [new OpenLayers.Control.Navigation()]
        },
        layers: [wms2, clone],
        extent: [-5, 35, 15, 55],
        items: [{
            xtype: "gx_opacityslider",
            layer: clone,
            complementaryLayer: wms2,
            changeVisibility: true,
            aggressive: true,
            vertical: true,
            height: 120,
            x: 10,
            y: 10,
            plugins: new GeoExt.LayerOpacitySliderTip()
        }]
    });
    
    var tree = new Ext.tree.TreePanel({
        width: 145,
        height: 300,
        renderTo: "tree",
        root: new GeoExt.tree.LayerContainer({
            layerStore: panel2.layers,
            expanded: true
        })
    });

});
