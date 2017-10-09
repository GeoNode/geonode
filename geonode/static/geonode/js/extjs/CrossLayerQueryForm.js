/**
 * Copyright (c) 2008-2012 The Open Planning Project
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @include widgets/FilterBuilder.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = CrossLayerQueryForm
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: CrossLayerQueryForm(config)
 *
 *    Plugin for performing cross layer queries
 */
gxp.plugins.CrossLayerQueryForm = Ext.extend(gxp.plugins.Tool, {
    hasSaveData: false,
    downloadData: null,
    /** api: ptype = gxp_crosslayerqueryform */
    ptype: "gxp_crosslayerqueryform",

    /** api: config[featureManager]
     *  ``String`` The id of the :class:`gxp.plugins.FeatureManager` to use
     *  with this tool.
     */
    featureManager: null,

    /** api: config[autoHide]
     *  ``Boolean`` Set to true if the output of this tool goes into an
     *  ``Ext.Window`` that should be hidden when the query result is
     *  available. Default is false.
     */
    autoHide: false,

    /** private: property[schema]
     *  ``GeoExt.data.AttributeStore``
     */
    schema: null,

    /** api: config[queryActionText]
     *  ``String``
     *  Text for query action (i18n).
     */
    queryActionText: "CrossQuery",

    /** api: config[cancelButtonText]
     *  ``String``
     *  Text for cancel button (i18n).
     */
    cancelButtonText: "Cancel",

    /** api: config[queryMenuText]
     *  ``String``
     *  Text for query menu item (i18n).
     */
    queryMenuText: "Cross layer query",

    /** api: config[queryActionTip]
     *  ``String``
     *  Text for query action tooltip (i18n).
     */
    queryActionTip: "Cross query selected layer",


    /** api: config[queryMsg]
     *  ``String``
     *  Text for query load mask (i18n).
     */
    queryMsg: "Querying...",

    /** api: config[noFeaturesTitle]
     *  ``String``
     *  Text for no features alert title (i18n)
     */
    noFeaturesTitle: "No Match",

    /** api: config[noFeaturesMsg]
     *  ``String``
     *  Text for no features alert message (i18n)
     */
    noFeaturesMessage: "Your query did not return any results.",

    /** api: config[actions]
     *  ``Object`` By default, this tool creates a "Query" action to trigger
     *  the output of this tool's form. Set to null if you want to include
     *  the form permanently in your layout.
     */

    /** api: config[outputAction]
     *  ``Number`` By default, the "Query" action will trigger this tool's
     *  form output. There is no need to change this unless you configure
     *  custom ``actions``.
     */
    outputAction: 0,

    /** api: crossLayerRecord
     *  ``Object``
     *  Store for cross layer records (i18n)
     */
    crossLayerRecord: {},

    constructor: function(config) {
        Ext.applyIf(config, {
            actions: [{
                text: this.queryActionText,
                menuText: this.queryMenuText,
                iconCls: "gxp-icon-find",
                tooltip: this.queryActionTip,
                disabled: true
            }]
        });
        gxp.plugins.CrossLayerQueryForm.superclass.constructor.apply(this, arguments);
    },

    /** api: method[addActions]
     */
    addActions: function(actions) {
        gxp.plugins.CrossLayerQueryForm.superclass.addActions.apply(this, arguments);
        // support custom actions
        if (this.actions) {
            var featureManager = this.target.tools[this.featureManager];
            //featureManager.maxFeatures = 10000;
            featureManager.maxFeatures = null;
            featureManager.on("layerchange",
                function(mgr, rec, schema) {
                    for (var i=this.actions.length-1; i>=0; --i) {
                        this.actions[i].setDisabled(!schema);
                    }
                }, this);
        }
    },

    /** api: method[getLayerSource]
     */
    getLayerSource: function(target) {
        var featureManager = target.tools[this.featureManager];
        var sourceId = featureManager.layerRecord.data.source;
        return target.layerSources[sourceId];
    },

    /** api: method[addFilterBuilder]
     */
    addFilterBuilder: function(layerTypeSchema, attrFieldSet) {
        if (attrFieldSet.hidden) {
            attrFieldSet.show();
        }
        attrFieldSet.removeAll();
        if (layerTypeSchema) {
            attrFieldSet.add({
                xtype: "gxp_filterbuilder",
                ref: "filterBuilder",
                attributes: layerTypeSchema,
                allowBlank: true,
                allowGroups: false
            });
            attrFieldSet.expand();
        } else {
            attrFieldSet.rendered && attrFieldSet.collapse();
        }
        attrFieldSet.doLayout();
    },

    /** api: method[crossLayerSelect]
     */
    crossLayerSelect: function(targetField, attrFieldSet, recordName) {
        var record = this.capGrid.capGridPanel.getSelectionModel().getSelected();
        if (record != undefined && record.get("queryable")) {
            targetField.setValue(record.get("name"));
            targetField.enable();
            this.capGrid.hide();
            this.getLayerSource(this.target).getSchema(record, function(schema) {
                this.addFilterBuilder(schema, attrFieldSet);
            }, this);
        }
        this.crossLayerRecord[recordName] = record;
    },

    /** api: method[showCapabilitiesGrid]
     */
    showCapabilitiesGrid: function(field, attrFieldSet, recordName) {
        if(!this.capGrid) {
            this.initCapGrid();
        }
        this.capGrid.capGridPanel.on('rowdblclick',
            Ext.createDelegate(this.crossLayerSelect, this,
                [field, attrFieldSet, recordName]), this,
                { single : true });
        this.capGrid.show();
    },

    /** api: method[initCapGrid]
     */
    initCapGrid: function() {
        var featureManager = this.target.tools[this.featureManager];
        var sourceId = featureManager.layerRecord.data.source;
        var source = this.target.layerSources[sourceId];

        var capGridPanel = new gxp.grid.CapabilitiesGrid({
            expander: null,
            ref: "../capGridPanel",
            sm: new Ext.grid.RowSelectionModel({singleSelect:true}),
            height: 300,
            width: 450,
            plugins: [],
            store: source.store,
            allowNewSources: false
        });

        var items = {
            xtype: "container",
            region: "center",
            layout: "vbox",
            items: [capGridPanel]
        };

        this.capGrid = new Ext.Window(Ext.apply({
            title: "Select layer for cross query",
            closeAction: "hide",
            layout: "border",
            height: 300,
            width: 650,
            modal: true,
            items: items,
            listeners: {
                hide: function(win) {
                    capGridPanel.getSelectionModel().clearSelections();
                },
                show: function(win) {
                    var sourceId = featureManager.layerRecord.data.source;
                    capGridPanel.reconfigure(this.target.layerSources[sourceId].store,
                                            capGridPanel.getColumnModel());
                },
                scope: this
            }
        }, this.initialConfig.outputConfig));

    },

    /** api: method[resetGridPanel]
     */
    resetGridPanel: function(queryForm) {
        queryForm.intersectCrossLayerField.reset();
        queryForm.intersectCrossLayerField.disable();
        queryForm.intersectAttributeFieldset.removeAll();
        queryForm.intersectAttributeFieldset.hide();
        /*queryForm.dWithinCrossLayerField.reset();
        queryForm.dWithinCrossLayerField.disable();
        queryForm.dWithinAttributeFieldset.removeAll();
        queryForm.dWithinAttributeFieldset.hide();*/
    },

    isNumeric: function (n) {
        return !isNaN(parseFloat(n)) && isFinite(n);
    },
    /** api: method[filterTemplate]
     */
    filterTemplate: function(attrFilter, filterType, params) {
        var featureManager = this.target.tools[this.featureManager];
        var record = this.crossLayerRecord[filterType];
        var filterStr = "INCLUDE";
        //console.log('attrFilter', attrFilter);
        if (attrFilter) {
            /*var attrFilterValue = (attrFilter.value);
            if(this.isNumeric(attrFilterValue)){
                attrFilter.value = parseFloat(attrFilterValue); 
            }*/
            filterStr = attrFilter.toString();
        }

        var filterFunc = new OpenLayers.Filter.Function({
            name: 'collectGeometries',
            params: [new OpenLayers.Filter.Function({
                name: 'queryCollection',
                params: [record.get("name"),
                        featureManager.featureStore.geometryName,
                        filterStr]
            })]
        });
        var filterQuery = new OpenLayers.Filter.Spatial({
            property: featureManager.featureStore.geometryName,
            type: filterType,
            value: filterFunc
        });
        Ext.apply(filterQuery, params);
        return filterQuery;
    },

    /** api: method[getattrFieldsetFilter]
     */
    getattrFieldsetFilter: function(attrFieldset) {
        var filter = "INCLUDE";
        if (attrFieldset.collapsed !== true) {
            var attributeFilter = attrFieldset.filterBuilder.getFilter();
            if (attributeFilter) {
                filter = attributeFilter.toString();
            }
        }
        return filter;
    },

    /** api: method[addOutput]
     */
    addOutput: function(config) {
        var featureManager = this.target.tools[this.featureManager];
        featureManager.style = {
            "all": new OpenLayers.Style(null, {
                rules: [new OpenLayers.Rule({
                    symbolizer: this.initialConfig.symbolizer || {
                        "Point": {
                            pointRadius: 4,
                            graphicName: "square",
                            fillColor: "blue",
                            fillOpacity: 1,
                            strokeWidth: 1,
                            strokeOpacity: 1,
                            graphicZIndex : 1000,
                            zIndex: 1000,
                            strokeColor: "#333333"
                        },
                        "Line": {
                            graphicZIndex : 1000,
                            zIndex: 1000,
                            strokeWidth: 4,
                            strokeOpacity: 1,
                            strokeColor: "#ff9933"
                        },
                        "Polygon": {
                            graphicZIndex : 1000,
                            zIndex: 1000,
                            strokeWidth: 2,
                            strokeOpacity: 1,
                            strokeColor: "#ff6633",
                            fillColor: "blue",
                            fillOpacity: 0.3
                        }
                    }
                })]
            }),
            "selected": new OpenLayers.Style(null, {
                rules: [new OpenLayers.Rule({symbolizer: {display: "none"}})]
            })
        };
        config = Ext.apply({
            tooltip: this.queryMenuText,
            title: this.queryMenuText,
            border: false,
            height: 450,
            width: 600,
            bodyStyle: "padding: 10px",
            layout: "form",
            autoScroll: true,
            items: [{
                xtype: "fieldset",
                ref: "intersectFieldset",
                title: "Intersects",
                checkboxToggle: true,
                collapsed: false,
                hideLabels: true,
                items: [{
                        xtype: "compositefield",
                        items: [{
                            xtype: "button",
                            //text: "Select Layer",
                            text: "Layer",
                            /*handler: function() {
                                this.showCapabilitiesGrid(
                                    queryForm.intersectCrossLayerField,
                                    queryForm.intersectAttributeFieldset,
                                    OpenLayers.Filter.Spatial.INTERSECTS);
                            },*/
                            scope: this
                        }, {
                            xtype: "textfield",
                            ref: "../../intersectCrossLayerField",
                            disabled: true,
                            readOnly: true
                        }, {
                            xtype: "button",
                            //text: "Add Layer",
                            title: this.queryActionTip,
                            tooltip: this.queryActionTip,
                            id: 'crossLayerQueryFromAddIcon',
                            iconMask:'true',
                            iconAlign:'top',
                            cls:'crossLayerQueryFromAddIcon',
                            iconCls: "gxp-icon-addlayers",
                            handler: function() {
                                this.showCapabilitiesGrid(
                                    queryForm.intersectCrossLayerField,
                                    queryForm.intersectAttributeFieldset,
                                    OpenLayers.Filter.Spatial.INTERSECTS);
                            },
                            scope: this
                        }]
                    }, {
                        xtype: "fieldset",
                        hidden: "true",
                        ref: "../intersectAttributeFieldset",
                        title: "Filter",
                        checkboxToggle: true
                    }
                ]
            /*}, {
                xtype: "fieldset",
                ref: "dWithinFieldset",
                title: "DWithin",
                checkboxToggle: true,
                collapsed: true,
                items: [{
                        xtype: "compositefield",
                        hideLabel: true,
                        items: [{
                            xtype: "button",
                            text: "Select Layer",
                            handler: function() {
                                this.showCapabilitiesGrid(queryForm.dWithinCrossLayerField,
                                    queryForm.dWithinAttributeFieldset,
                                    OpenLayers.Filter.Spatial.DWITHIN);
                            },
                            scope: this
                        }, {
                            xtype: "textfield",
                            ref: "../../dWithinCrossLayerField",
                            disabled: true,
                            readOnly: true
                        }]
                    },
                    {
                        xtype: "textfield",
                        ref: "../dWithinDistanceField",
                        fieldLabel: "Distance (km)",
                        width: 120,
                        value: "100",
                        readOnly: false
                    }, {
                        xtype: "fieldset",
                        hidden: "true",
                        ref: "../dWithinAttributeFieldset",
                        title: "Filter",
                        checkboxToggle: true
                    }
                ]*/
            }],
            bbar: ["->", {
                text: this.cancelButtonText,
                iconCls: "cancel",
                handler: function() {
                    var ownerCt = this.outputTarget ? queryForm.ownerCt :
                        queryForm.ownerCt.ownerCt;
                    if (ownerCt && ownerCt instanceof Ext.Window) {
                        ownerCt.hide();
                    } else {
                        addAttributeFilter(
                            featureManager,
                            featureManager.layerRecord,
                            featureManager.schema
                        );
                    }
                }
            }, {
                text: "Download CSV",
                iconCls: "icon-save",
                //disabled: !this.hasSaveData,
                handler: function() {
                    var filters = [];
                    if (queryForm.intersectFieldset.collapsed !== true &&
                            queryForm.intersectCrossLayerField.disabled !== true) {
                        var intersectFilter = this.filterTemplate(
                                        queryForm.intersectAttributeFieldset.filterBuilder.getFilter(),
                                        OpenLayers.Filter.Spatial.INTERSECTS);
                        filters.push(intersectFilter);
                    }
                    if (filters.length > 0) {
                        featureManager.loadFeatures(filters.length > 1 ?
                            new OpenLayers.Filter.Logical({
                                type: OpenLayers.Filter.Logical.AND,
                                filters: filters
                            }) :
                            filters[0]
                        );
                    }
                    this.hasSaveData = true;
                    
                    /*var store = this.downloadData;
                    console.log(store);
                    // check store is avalivale or not
                    if(store !== null && store.getCount() > 0){
                        var jsonData = Ext.encode(Ext.pluck(store.data.items, 'data'));
                        console.log(jsonData);
                    } else {
                        Ext.Msg.show({
                            title: 'Warning',
                            msg: '',
                            buttons: Ext.Msg.OK,
                            icon: Ext.Msg.INFO
                        });
                    }*/
                },
                scope: this
            }, {
                text: this.queryActionText,
                iconCls: "gxp-icon-find",
                handler: function() {
                    var filters = [];
                    if (queryForm.intersectFieldset.collapsed !== true &&
                            queryForm.intersectCrossLayerField.disabled !== true) {
                        var intersectFilter = this.filterTemplate(
                                        queryForm.intersectAttributeFieldset.filterBuilder.getFilter(),
                                        OpenLayers.Filter.Spatial.INTERSECTS);
                        filters.push(intersectFilter);
                    }
                    /*if (queryForm.dWithinFieldset.collapsed !== true &&
                            queryForm.dWithinCrossLayerField.disabled !== true) {
                        var dWithinFilter = this.filterTemplate(
                                    queryForm.dWithinAttributeFieldset.filterBuilder.getFilter(),
                                    OpenLayers.Filter.Spatial.DWITHIN,
                                    {distance: queryForm.dWithinDistanceField.getValue()});
                        filters.push(dWithinFilter);
                    }*/
                    if (filters.length > 0) {
                        featureManager.loadFeatures(filters.length > 1 ?
                            new OpenLayers.Filter.Logical({
                                type: OpenLayers.Filter.Logical.AND,
                                filters: filters
                            }) :
                            filters[0]
                        );
                    }
                    this.hasSaveData = false;
                },
                scope: this
            }]
        }, config || {});
        var queryForm = gxp.plugins.CrossLayerQueryForm.superclass.addOutput.call(this, config);

        featureManager.on({
            "layerchange": function(mgr, rec, schema) {
                new Ext.LoadMask(queryForm.getEl(), {
                    store: featureManager.featureStore,
                    msg: this.queryMsg
                }).hide();
                this.resetGridPanel(queryForm);
            },
            "beforequery": function() {
                new Ext.LoadMask(queryForm.getEl(), {
                    store: featureManager.featureStore,
                    msg: this.queryMsg
                }).show();
            },
            "query": function(tool, store) {
                if (store) {
                    if (this.target.tools[this.featureManager].featureStore !== null) {
                        store.getCount() || Ext.Msg.show({
                            title: this.noFeaturesTitle,
                            msg: this.noFeaturesMessage,
                            buttons: Ext.Msg.OK,
                            icon: Ext.Msg.INFO
                        });
                        if (this.autoHide) {
                            var ownerCt = this.outputTarget ? queryForm.ownerCt :
                                queryForm.ownerCt.ownerCt;
                            ownerCt instanceof Ext.Window && ownerCt.hide();
                        }
                        if(this.hasSaveData){
                            var tableRows = [];
                            var tableHeader = [];
                            
                            var searchResult = store.data.items;
                            if(searchResult.length > 0 && searchResult[0] !== undefined){
                                var layerName = searchResult[0].data.feature.fid;
                                layerName = layerName.replace('.1', '');
                                // get table header
                                var featureData = searchResult[0].data.feature.data;
                                if ((featureData instanceof Object) && !(featureData instanceof Array)) {
                                    var keys = Object.keys(featureData);
                                    var columnsLen = keys.length;
                                    var headerColumnsLen = columnsLen;
                                    for (var j = 0; j < columnsLen; j++) {
                                        var header = keys[j];
                                        if (tableHeader.length < headerColumnsLen) {
                                            tableHeader.push(header);
                                        }
                                    }
                                }
                                // table row adding
                                for(var i=0; i<searchResult.length; i++){
                                    var result = searchResult[i];
                                    var featureData = result.data.feature.data;
                                    tableRows.push(featureData);
                                }
                            }
                            this.downloadCSV(tableRows, { filename: layerName+"-cross-layer.csv" });
                            //var jsonData = Ext.encode(Ext.pluck(store.data.items, 'data'));
                            //console.log(store);
                            //console.log(tableHeader, tableRows);
                        } else {
                            featureManager.showLayer();
                            featureManager.visible();
                            featureManager.raiseLayer();
                        }
                    }
                }
            },
            scope: this
        });

        return queryForm;
    },

    convertArrayOfObjectsToCSV: function (args) {
        var result, ctr, keys, columnDelimiter, lineDelimiter, data;

        data = args.data || null;
        if (data == null || !data.length) {
            return null;
        }

        columnDelimiter = args.columnDelimiter || ',';
        lineDelimiter = args.lineDelimiter || '\n';

        var headerItem = [];
        var keyItems = Object.keys(data[0]);
        for(var i=0; i<keyItems.length; i++){
            var item = keyItems[i];
            item = item.replace('centerDistance', 'Distance')
                .replace('pro_', '')
                .replace('_perty','');
            headerItem.push(item);
        }
        keys = Object.keys(data[0]);

        result = '';
        result += headerItem.join(columnDelimiter);
        result += lineDelimiter;

        data.forEach(function (item) {
            ctr = 0;
            keys.forEach(function (key) {
                if (ctr > 0)
                    result += columnDelimiter;

                result += item[key];
                ctr++;
            });
            result += lineDelimiter;
        });

        return result;
    },

    downloadCSV: function (stockData, args) {
        var data, filename, link;

        var csv = this.convertArrayOfObjectsToCSV({
            data: stockData
        });
        if (csv == null)
            return;

        filename = args.filename || 'export.csv';

        if (!csv.match(/^data:text\/csv/i)) {
            csv = 'data:text/csv;charset=utf-8,' + csv;
        }
        data = encodeURI(csv);

        link = document.createElement('a');
        link.setAttribute('href', data);
        link.setAttribute('download', filename);
        //link.click();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
});

Ext.preg(gxp.plugins.CrossLayerQueryForm.prototype.ptype, gxp.plugins.CrossLayerQueryForm);