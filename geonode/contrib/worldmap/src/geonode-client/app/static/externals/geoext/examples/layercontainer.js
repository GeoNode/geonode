/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[layercontainer]
 *  Layer Tree
 *  ----------
 *  Create a layer tree with a LayerContainer.
 */

var store, tree, panel;
Ext.onReady(function() {
    
    // create a new WMS capabilities store
    store = new GeoExt.data.WMSCapabilitiesStore({
        url: "data/wmscap.xml"
    });
    // load the store with records derived from the doc at the above url
    store.load();

    // create a grid to display records from the store
    var grid = new Ext.grid.GridPanel({
        title: "WMS Capabilities",
        store: store,
        cm: new Ext.grid.ColumnModel([
            {header: "Name", dataIndex: "name", sortable: true},
            {id: "title", header: "Title", dataIndex: "title", sortable: true}
        ]),
        sm: new Ext.grid.RowSelectionModel({singleSelect:true}),
        autoExpandColumn: "title",
        renderTo: "capgrid",
        height: 300,
        width: 350,
        floating: true,
        x: 10,
        y: 0,
        bbar: ["->", {
            text: "Add Layer",
            handler: function() {
                var record = grid.getSelectionModel().getSelected();
                if(record) {
                    var copy = record.copy();
                    // Ext 3.X does not allow circular references in objects passed 
                    // to record.set 
                    copy.data["layer"] = record.getLayer();
                    copy.getLayer().mergeNewParams({
                        format: "image/png",
                        transparent: "true"
                    });
                    panel.layers.add(copy);
                    panel.map.zoomToExtent(
                        OpenLayers.Bounds.fromArray(copy.get("llbbox"))
                    );
                }
            }
        }]
    });
    
    // create a map panel
    panel = new GeoExt.MapPanel({
        renderTo: "mappanel",
        width: 350,
        height: 300,
        floating: true,
        x: 570,
        y: 0
    });
    
    tree = new Ext.tree.TreePanel({
        renderTo: "tree",
        root: new GeoExt.tree.LayerContainer({
            text: 'Map Layers',
            layerStore: panel.layers,
            leaf: false,
            expanded: true
        }),
        enableDD: true,
        width: 170,
        height: 300,
        floating: true,
        x: 380,
        y: 0
    });
    

});
