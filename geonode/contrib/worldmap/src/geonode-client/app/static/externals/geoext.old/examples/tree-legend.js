/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

 /** api: example[tree-legend]
  *  Tree Legend
  *  -----------
  *  Render layer nodes with legends.
  */

// custom layer node UI class
var LayerNodeUI = Ext.extend(
    GeoExt.tree.LayerNodeUI,
    new GeoExt.tree.TreeNodeUIEventMixin()
);

Ext.onReady(function() {
    var mapPanel = new GeoExt.MapPanel({
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

    var tree = new Ext.tree.TreePanel({
        region: "east",
        title: "Layers",
        width: 250,
        autoScroll: true,
        enableDD: true,
        // apply the tree node component plugin to layer nodes
        plugins: [{
            ptype: "gx_treenodecomponent"
        }],
        loader: {
            applyLoader: false,
            uiProviders: {
                "custom_ui": LayerNodeUI
            }
        },
        root: {
            nodeType: "gx_layercontainer",
            loader: {
                baseAttrs: {
                    uiProvider: "custom_ui"
                },
                createNode: function(attr) {
                    // add a WMS legend to each node created
                    attr.component = {
                        xtype: "gx_wmslegend",
                        layerRecord: mapPanel.layers.getByLayer(attr.layer),
                        showTitle: false,
                        // custom class for css positioning
                        // see tree-legend.html
                        cls: "legend"
                    }
                    return GeoExt.tree.LayerLoader.prototype.createNode.call(this, attr);
                }
            }
        },
        rootVisible: false,
        lines: false
    });

    new Ext.Viewport({
        layout: "fit",
        hideBorders: true,
        items: {
            layout: "border",
            items: [
                mapPanel, tree, {
                    contentEl: desc,
                    region: "west",
                    width: 250,
                    bodyStyle: {padding: "5px"}
                }
            ]
        }
    });
});
