/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

Ext.namespace("GeoExt.examples");

// this function takes action based on the "action"
// parameter, it is used as a listener to layer
// nodes' "action" events
GeoExt.examples.onAction = function(node, action, evt) {
    var layer = node.layer;
    switch(action) {
    case "down":
        layer.map.raiseLayer(layer, -1);
        break;
    case "up":
        layer.map.raiseLayer(layer, +1);
        break;
    case "delete":
        layer.destroy();
        break;
    }
};

// custom layer node UI class
GeoExt.examples.LayerNodeUI = Ext.extend(
    GeoExt.tree.LayerNodeUI,
    new GeoExt.tree.TreeNodeUIEventMixin()
);

Ext.onReady(function() {
    Ext.QuickTips.init();

    // the map panel
    var mapPanel = new GeoExt.MapPanel({
        border: true,
        region: "center",
        center: [146.1569825, -41.6109735],
        zoom: 6,
        layers: [
            new OpenLayers.Layer.WMS("Tasmania State Boundaries",
                "http://demo.opengeo.org/geoserver/wms", {
                    layers: "topp:tasmania_state_boundaries"
                }, {
                    buffer: 0,
                    // exclude this layer from layer container nodes
                    displayInLayerSwitcher: false
               }),
            new OpenLayers.Layer.WMS("Water",
                "http://demo.opengeo.org/geoserver/wms", {
                    layers: "topp:tasmania_water_bodies",
                    transparent: true,
                    format: "image/gif"
                }, {
                    buffer: 0
                }),
            new OpenLayers.Layer.WMS("Cities",
                "http://demo.opengeo.org/geoserver/wms", {
                    layers: "topp:tasmania_cities",
                    transparent: true,
                    format: "image/gif"
                }, {
                    buffer: 0
                }),
            new OpenLayers.Layer.WMS("Tasmania Roads",
                "http://demo.opengeo.org/geoserver/wms", {
                    layers: "topp:tasmania_roads",
                    transparent: true,
                    format: "image/gif"
                }, {
                    buffer: 0
                })
        ]
    });

    // the layer tree panel. In this tree the node actions are set using 
    // the loader's "baseAttrs" property.
    var tree = new Ext.tree.TreePanel({
        region: "west",
        width: 250,
        title: "Layer Tree",
        loader: {
            applyLoader: false,
            uiProviders: {
                "ui": GeoExt.examples.LayerNodeUI
            }
        },
        // apply the tree node actions plugin to layer nodes
        plugins: [{
            ptype: "gx_treenodeactions",
            listeners: {
                action: GeoExt.examples.onAction
            }
        }],
        root: {
            nodeType: "gx_layercontainer",
            loader: {
                baseAttrs: {
                    radioGroup: "radiogroup",
                    uiProvider: "ui",
                    actions: [{
                        action: "delete",
                        qtip: "delete"
                    }, {
                        action: "up",
                        qtip: "move up",
                        update: function(el) { 
                            // "this" references the tree node 
                            var layer = this.layer, map = layer.map; 
                            if (map.getLayerIndex(layer) == map.layers.length - 1) { 
                                el.addClass('disabled'); 
                            } else { 
                                el.removeClass('disabled'); 
                            } 
                        } 
                    }, { 
                        action: "down", 
                        qtip: "move down", 
                        update: function(el) { 
                            // "this" references the tree node 
                            var layer = this.layer, map = layer.map; 
                            if (map.getLayerIndex(layer) == 1) { 
                                el.addClass('disabled'); 
                            } else { 
                                el.removeClass('disabled'); 
                            } 
                        } 
                    }]
                }
            }
        },
        rootVisible: false,
        lines: false
    });

    // the viewport
    new Ext.Viewport({
        layout: "fit",
        hideBorders: true,
        items: {
            layout: "border",
            deferredRender: false,
            items: [
                mapPanel,
                tree, {
                region: "east",
                contentEl: "desc",
                width: 250
            }]
        }
    });
});
