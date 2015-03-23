/**
 * Copyright (c) 2008-2011 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[attributes]
 *  Attribute Store & Reader
 *  ------------------------
 *  Create records with attribute types and values with an AttributeStore.
 */

var store;
Ext.onReady(function() {
    
    // create a new attributes store
    store = new GeoExt.data.AttributeStore({
        url: "data/describe_feature_type.xml"
    });
    store.load();

    // create a grid to display records from the store
    var grid = new Ext.grid.GridPanel({
        title: "Feature Attributes",
        store: store,
        cm: new Ext.grid.ColumnModel([
            {id: "name", header: "Name", dataIndex: "name", sortable: true},
            {id: "type", header: "Type", dataIndex: "type", sortable: true}
        ]),
        sm: new Ext.grid.RowSelectionModel({singleSelect:true}),
        autoExpandColumn: "name",
        renderTo: document.body,
        height: 300,
        width: 350
    });    

});
