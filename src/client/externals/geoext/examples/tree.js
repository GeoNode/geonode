/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

var mapPanel;
Ext.onReady(function() {
    // using OpenLayers.Format.JSON to create a nice formatted string of the
    // configuration for editing it in the UI
    var treeConfig = new OpenLayers.Format.JSON().write([{
        nodeType: "gx_baselayercontainer"
    }, {
        nodeType: "gx_overlaylayercontainer",
        // render the nodes inside this container with a radio button,
        // and assign them the group "foo"
        loader: {
            baseAttrs: {radioGroup: "foo"}
        }
    }, {
        nodeType: "gx_layer",
        layer: "Tasmania Roads"
    }], true);

    mapPanel = new GeoExt.MapPanel({
        border: true,
        region: "center",
        // we do not want all overlays, to try the OverlayLayerContainer
        map: new OpenLayers.Map({allOverlays: false}),
        center: [146.1569825, -41.6109735],
        zoom: 6,
        layers: [
            new OpenLayers.Layer.WMS("Global Imagery",
                "http://demo.opengeo.org/geoserver/wms", {
                    layers: "bluemarble"
                }, {
                    buffer: 0,
                    visibility: false
                }),
            new OpenLayers.Layer.WMS("Tasmania State Boundaries",
                "http://demo.opengeo.org/geoserver/wms", {
                    layers: "topp:tasmania_state_boundaries"
                }, {
                    buffer: 0
               }),
            new OpenLayers.Layer.WMS("Water",
                "http://demo.opengeo.org/geoserver/wms", {
                    layers: "topp:tasmania_water_bodies",
                    transparent: true,
                    format: "image/gif"
                }, {
                    isBaseLayer: false,
                    buffer: 0
                }),
            new OpenLayers.Layer.WMS("Cities",
                "http://demo.opengeo.org/geoserver/wms", {
                    layers: "topp:tasmania_cities",
                    transparent: true,
                    format: "image/gif"
                }, {
                    isBaseLayer: false,
                    buffer: 0
                }),
            new OpenLayers.Layer.WMS("Tasmania Roads",
                "http://demo.opengeo.org/geoserver/wms", {
                    layers: "topp:tasmania_roads",
                    transparent: true,
                    format: "image/gif"
                }, {
                    isBaseLayer: false,
                    buffer: 0,
                    // exclude this layer from layer container nodes
                    displayInLayerSwitcher: false
                })
        ]
    });
    
    // dialog for editing the tree configuration
    var treeConfigWin = new Ext.Window({
        layout: "fit",
        hideBorders: true,
        closeAction: "hide",
        width: 300,
        height: 400,
        title: "Tree Configuration",
        items: [{
            xtype: "form",
            layout: "fit",
            items: [{
                id: "treeconfig",
                xtype: "textarea"
            }],
            buttons: [{
                text: "Save",
                handler: function() {
                    var value = Ext.getCmp("treeconfig").getValue()
                    try {
                        var root = tree.getRootNode();
                        root.attributes.children = Ext.decode(value);
                        tree.getLoader().load(root);
                    } catch(e) {
                        alert("Invalid JSON");
                        return;
                    }
                    treeConfig = value;
                    treeConfigWin.hide();
                }
            }, {
                text: "Cancel",
                handler: function() {
                    treeConfigWin.hide();
                }
            }]
        }]
    });
    
    var toolbar = new Ext.Toolbar({
        items: [{
            text: "Show/Edit Tree Config",
            handler: function() {
                treeConfigWin.show();
                Ext.getCmp("treeconfig").setValue(treeConfig);
            }
        }]
    });
    
    var tree = new Ext.tree.TreePanel({
        border: true,
        region: "west",
        title: "Layers",
        width: 200,
        split: true,
        collapsible: true,
        collapseMode: "mini",
        autoScroll: true,
        loader: new Ext.tree.TreeLoader({
            applyLoader: false
        }),
        root: {
            nodeType: "async",
            children: Ext.decode(treeConfig)
        },
        rootVisible: false,
        lines: false,
        bbar: toolbar
    });
    
    // the layer node's radio button with its radiochange event can be used
    // to set an active layer.
    var registerRadio = function(node){
        if(!node.hasListener("radiochange")) {
            node.on("radiochange", function(node){
                alert(node.layer.name + " is now the the active layer.");
            });
        }
    }
    tree.on({
        "insert": registerRadio,
        "append": registerRadio,
        scope: this
    });
    
    new Ext.Viewport({
        layout: "fit",
        hideBorders: true,
        items: {
            layout: "border",
            deferredRender: false,
            items: [mapPanel, tree, {
                contentEl: "desc",
                region: "east",
                bodyStyle: {"padding": "5px"},
                collapsible: true,
                collapseMode: "mini",
                split: true,
                width: 200,
                title: "Description"
            }]
        }
    });
});
