/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 *
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[wms-tree]
 *  WMS Capabilities Tree
 *  ---------------------
 *  Create a tree loader from WMS capabilities documents.
 */
var tree, mapPanel;

Ext.onReady(function() {

    var root = new Ext.tree.AsyncTreeNode({
        text: 'GeoServer Demo WMS',
        loader: new GeoExt.tree.WMSCapabilitiesLoader({
            url: 'data/wmscap.xml',
            layerOptions: {buffer: 0, singleTile: true, ratio: 1},
            layerParams: {'TRANSPARENT': 'TRUE'},
            // customize the createNode method to add a checkbox to nodes
            createNode: function(attr) {
                attr.checked = attr.leaf ? false : undefined;
                return GeoExt.tree.WMSCapabilitiesLoader.prototype.createNode.apply(this, [attr]);
            }
        })
    });

    tree = new Ext.tree.TreePanel({
        root: root,
        region: 'west',
        width: 250,
        listeners: {
            // Add layers to the map when ckecked, remove when unchecked.
            // Note that this does not take care of maintaining the layer
            // order on the map.
            'checkchange': function(node, checked) { 
                if (checked === true) {
                    mapPanel.map.addLayer(node.attributes.layer); 
                } else {
                    mapPanel.map.removeLayer(node.attributes.layer);
                }
            }
        }
    });

    mapPanel = new GeoExt.MapPanel({
        zoom: 2,
        layers: [
            new OpenLayers.Layer.WMS("Global Imagery",
                "http://maps.opengeo.org/geowebcache/service/wms", 
                {layers: "bluemarble"},
                {buffer: 0}
            )
        ],
        region: 'center'
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
