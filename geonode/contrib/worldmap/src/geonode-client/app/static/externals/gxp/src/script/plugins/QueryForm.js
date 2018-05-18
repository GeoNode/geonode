/**
 * Copyright (c) 2008-2011 The Open Planning Project
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
 *  class = QueryForm
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: QueryForm(config)
 *
 *    Plugin for performing queries on feature layers
 *    TODO Replace this tool with something that is less like GeoEditor and
 *    more like filtering.
 */
gxp.plugins.QueryForm = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_queryform */
    ptype: "gxp_queryform",

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
    queryActionText: "Query",
    
    /** api: config[cancelButtonText]
     *  ``String``
     *  Text for cancel button (i18n).
     */
    cancelButtonText: "Cancel",

    /** api: config[queryMenuText]
     *  ``String``
     *  Text for query menu item (i18n).
     */
    queryMenuText: "Query layer",

    /** api: config[queryActionTip]
     *  ``String``
     *  Text for query action tooltip (i18n).
     */
    queryActionTip: "Query the selected layer",

    /** api: config[queryByLocationText]
     *  ``String``
     *  Text for query by location (i18n).
     */
    queryByLocationText: "Query by current map extent",

    /** api: config[queryByAttributesText]
     *  ``String``
     *  Text for query by attributes (i18n).
     */
    queryByAttributesText: "Query by attributes",
    
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
    
    /** api: config[autoExpand]
     *  ``String`` If setto the id of a container, the container will be
     *  expanded when the Query Form is enabled, and collapsed when it is
     *  disabled. Once the user manually expands/collapses the contaienr, the
     *  user setting will stick for the current session.
     */
    autoExpand: null,
    
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
        gxp.plugins.QueryForm.superclass.constructor.apply(this, arguments);
    },
    
    /** api: method[addActions]
     */
    addActions: function(actions) {
        gxp.plugins.QueryForm.superclass.addActions.apply(this, arguments);
        // support custom actions
        if (this.actionTarget !== null && this.actions) {
            this.target.tools[this.featureManager].on("layerchange", function(mgr, rec, schema) {
                for (var i=this.actions.length-1; i>=0; --i) {
                    this.actions[i].setDisabled(!schema);
                }
            }, this);
        }
    },

    /** api: method[addOutput]
     */
    addOutput: function(config) {
        var featureManager = this.target.tools[this.featureManager];

        config = Ext.apply({
            border: false,
            bodyStyle: "padding: 10px",
            layout: "form",
            width: 320,
            autoScroll: true,
            items: [{
                xtype: "fieldset",
                ref: "spatialFieldset",
                title: this.queryByLocationText,
                anchor: "97%",
                // This fieldset never expands
                style: "margin-bottom:0; border-left-color:transparent; border-right-color:transparent; border-width:1px 1px 0 1px; padding-bottom:0",
                checkboxToggle: true
            }, {
                xtype: "fieldset",
                ref: "attributeFieldset",
                title: this.queryByAttributesText,
                anchor: "97%",
                style: "margin-bottom:0",
                checkboxToggle: true
            }],
            bbar: ["->", {
                text: this.cancelButtonText,
                iconCls: "cancel",
                handler: function() {
                    var ownerCt = this.outputTarget ? queryForm.ownerCt :
                        queryForm.ownerCt.ownerCt;
                    if (ownerCt && ownerCt instanceof Ext.Window) {
                        ownerCt.hide();
                    }
                    addFilterBuilder(
                        featureManager, featureManager.layerRecord,
                        featureManager.schema
                    );
                    featureManager.loadFeatures();
                }
            }, {
                text: this.queryActionText,
                iconCls: "gxp-icon-find",
                handler: function() {
                    var filters = [];
                    if (queryForm.spatialFieldset.collapsed !== true) {
                        filters.push(new OpenLayers.Filter.Spatial({
                            type: OpenLayers.Filter.Spatial.BBOX,
                            property: featureManager.featureStore.geometryName,
                            value: this.target.mapPanel.map.getExtent()
                        }));
                    }
                    if (queryForm.attributeFieldset.collapsed !== true) {
                        var attributeFilter = queryForm.filterBuilder.getFilter();
                        attributeFilter && filters.push(attributeFilter);
                    }
                    featureManager.loadFeatures(filters.length > 1 ?
                        new OpenLayers.Filter.Logical({
                            type: OpenLayers.Filter.Logical.AND,
                            filters: filters
                        }) :
                        filters[0]
                    );
                },
                scope: this
            }]
        }, config || {});
        var queryForm = gxp.plugins.QueryForm.superclass.addOutput.call(this, config);
        
        var expandContainer = null, userExpand = true;
        if (this.autoExpand) {
            expandContainer = Ext.getCmp(this.autoExpand);
            function stopAutoExpand() {
                if (userExpand) {
                    expandContainer.un('expand', stopAutoExpand);
                    expandContainer.un('collapse', stopAutoExpand);
                    expandContainer = null;
                }
                userExpand = true;
            }
            expandContainer.on({
                'expand': stopAutoExpand,
                'collapse': stopAutoExpand
            });
        }
        var addFilterBuilder = function(mgr, rec, schema) {
            queryForm.attributeFieldset.removeAll();
            queryForm.setDisabled(!schema);
            if (expandContainer) {
                userExpand = false;
                expandContainer[schema ? 'expand' : 'collapse']();
            }
            if (schema) {
                queryForm.attributeFieldset.add({
                    xtype: "gxp_filterbuilder",
                    ref: "../filterBuilder",
                    attributes: schema,
                    allowBlank: true,
                    allowGroups: false
                });
                queryForm.spatialFieldset.expand();
                queryForm.attributeFieldset.expand();
            } else {
                queryForm.attributeFieldset.rendered && queryForm.attributeFieldset.collapse();
                queryForm.spatialFieldset.rendered && queryForm.spatialFieldset.collapse();
            }
            queryForm.attributeFieldset.doLayout();
        };
        featureManager.on("layerchange", addFilterBuilder);
        addFilterBuilder(featureManager,
            featureManager.layerRecord, featureManager.schema
        );
        
        featureManager.on({
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
                    }
                }
            },
            scope: this
        });
        
        return queryForm;
    }
        
});

Ext.preg(gxp.plugins.QueryForm.prototype.ptype, gxp.plugins.QueryForm);
