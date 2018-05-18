/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

var classifier, grid;
Ext.onReady(function() {

    var store = new Ext.data.GroupingStore({
        groupField: "group",
        reader: new gxp.data.RuleGroupReader()
    });
    
    classifier = new gxp.data.FeatureTypeClassifier({
        store: store,
        layerName: "usa:states"
    });

    grid = new Ext.grid.GridPanel({
        width: 420,
        height: 230,
        colModel: new Ext.grid.ColumnModel({
            columns: [
                {dataIndex: "symbolizers", width: 26, fixed: true, xtype: "gx_symbolizercolumn"},
                {header: "Label", dataIndex: "label", width: 120, fixed: true},
                {header: "Filter", dataIndex: "filter"},
                {dataIndex: "group", header: "Group", hidden: true}
            ]
        }),
        store: store,
        renderTo: "grid",
        view: new Ext.grid.GroupingView({
            autoFill: true,
            startCollapsed: true,
            // custom grouping text template to display the number of items per group
            groupTextTpl: '{text} ({[values.rs.length]} {[values.rs.length > 1 ? "Items" : "Item"]})'
        }),
        tbar: [{
            id: "classify",
            text: "Reclassify",
            disabled: true,
            handler: function() {
                classifier.classify("Population", "graduated", ["PERSONS", 4, "NATURAL_BREAKS"]);
            }
        }]
    });

    Ext.Ajax.request({
        method: "GET",
        url: "data/getstyles.xml",
        success: function(response) {
            var sld = new OpenLayers.Format.SLD({
                multipleSymbolizers: true
            }).read(response.responseText);
            store.loadData(sld.namedLayers["usa:states"].userStyles[0]);
            Ext.getCmp("classify").enable();
        }
    });    
        
});

Ext.USE_NATIVE_JSON = true;
