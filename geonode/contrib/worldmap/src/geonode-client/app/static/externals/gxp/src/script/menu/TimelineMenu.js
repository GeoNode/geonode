/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires widgets/form/FilterField.js
 */

/** api: (define)
 *  module = gxp.menu
 *  class = TimelineMenu
 *  base_link = `Ext.menu.Menu <http://extjs.com/deploy/dev/docs/?class=Ext.menu.Menu>`_
 */
Ext.namespace("gxp.menu");

/** api: constructor
 *  .. class:: TimelineMenu(config)
 *
 *    A menu to control layer visibility for the timeline. Can also be used
 *    to select the field to display in the timeline, as well as filtering
 *    the events to show in the timeline.
 */   
gxp.menu.TimelineMenu = Ext.extend(Ext.menu.Menu, {

    /** i18n */
    filterLabel: "Filter",
    attributeLabel: "Label",
    showNotesText: "Show notes",

    /** api: config[layers]
     *  ``GeoExt.data.LayerStore``
     *  The store containing layer records to be viewed in this menu.
     */
    layers: null,

    /** api: config[subMenuSize]
     *  ``Array`` The width and height of the sub menu form panel.
     */
    subMenuSize: [350, 60],

    /** private: method[initComponent]
     *  Private method called to initialize the component.
     */
    initComponent: function() {
        gxp.menu.TimelineMenu.superclass.initComponent.apply(this, arguments);
        this.timelinePanel = this.timelineTool && this.timelineTool.getTimelinePanel();
        this.layers.on("add", this.onLayerAddOrRemove, this);
        this.layers.on("remove", this.onLayerAddOrRemove, this);
        this.onLayerAddOrRemove();
    },

    /** private: method[onRender]
     *  Private method called during the render sequence.
     */
    onRender : function(ct, position) {
        gxp.menu.TimelineMenu.superclass.onRender.apply(this, arguments);
    },

    /** private: method[beforeDestroy]
     *  Private method called during the destroy sequence.
     */
    beforeDestroy: function() {
        if (this.layers && this.layers.on) {
            this.layers.un("add", this.onLayerAddOrRemove, this);
            this.layers.un("remove", this.onLayerAddOrRemove, this);
        }
        delete this.layers;
        gxp.menu.TimelineMenu.superclass.beforeDestroy.apply(this, arguments);
    },


    
    /** private: method[onLayerAddOrRemove]
     *  Listener called when records are added to the layer store.
     */
    onLayerAddOrRemove: function() {
        this.removeAll();
        if (this.timelinePanel.annotationsRecord) {
            var record = this.timelinePanel.annotationsRecord;
            var key = this.timelinePanel.getKey(record);
            this.add(new Ext.menu.CheckItem({
                text: this.showNotesText,
                checked: (this.timelinePanel.layerLookup[key] && this.timelinePanel.layerLookup[key].visible) || true,
                listeners: {
                    checkchange: function(item, checked) {
                        this.timelinePanel.setLayerVisibility(item, checked, record, false);
                    },
                    scope: this
                }
            }));
        }
        this.layers.each(function(record) {
            var layer = record.getLayer();
            if(layer.displayInLayerSwitcher && layer.dimensions && layer.dimensions.time) {
                var key = this.timelinePanel.getKey(record);
                var schema = this.timelinePanel.schemaCache[key];
                var item = new Ext.menu.CheckItem({
                    text: record.get("title"),
                    checked: (this.timelinePanel.layerLookup[key] && this.timelinePanel.layerLookup[key].visible) || false,
                    menu: new Ext.menu.Menu({
                        plain: true,
                        style: {
                            overflow: 'visible'
                        },
                        showSeparator: false,
                        items: [{
                            xtype: 'container',
                            width: this.subMenuSize[0],
                            height: this.subMenuSize[1], 
                            layout:'vbox',
                            defaults: {
                                border: false
                            },
                            layoutConfig: {
                                align: 'stretch',
                                pack: 'start'
                            },
                            items: [{
                                xtype: 'form',
                                labelWidth: 75,
                                height: 30,
                                items: [{
                                    xtype: 'combo',
                                    forceSelection: true,
                                    getListParent: function() {
                                        return this.el.up('.x-menu');
                                    },
                                    store: schema, 
                                    mode: 'local',
                                    triggerAction: 'all',
                                    value: this.timelinePanel.layerLookup[key] ? this.timelinePanel.layerLookup[key].titleAttr : null,
                                    listeners: {
                                        "select": function(combo) {
                                            this.timelinePanel.setTitleAttribute(record, combo.getValue());
                                        },
                                        scope: this
                                    },
                                    displayField: "name", 
                                    valueField: "name", 
                                    fieldLabel: this.attributeLabel
                                }]
                            }, {
                                xtype: 'container',
                                layout: 'hbox',
                                id: 'gxp_timemenufilter',
                                layoutConfig: {
                                    align: 'stretch',
                                    pack: 'start'
                                },
                                defaults: {
                                    border: false
                                },
                                items: [{
                                    width: 25,
                                    xtype: 'form',
                                    layout: 'fit',
                                    items: [{
                                        xtype: 'checkbox',
                                        checked: (this.timelinePanel.layerLookup[key] && this.timelinePanel.layerLookup[key].clientSideFilter !== undefined),
                                        ref: "../applyFilter",
                                        listeners: {
                                            'check': function(cb, checked) { 
                                                var field = Ext.getCmp('gxp_timemenufilter').filter;
                                                if (field.isValid()) {
                                                    this.timelinePanel.applyFilter(record, field.filter, checked);
                                                }
                                            },
                                            scope: this
                                        }
                                    }]
                                }, {
                                    flex: 1,
                                    xtype: 'form',
                                    labelWidth: 75,
                                    items: [{
                                        xtype: "gxp_filterfield",
                                        ref: "../filter",
                                        filter: this.timelinePanel.layerLookup[key] ? this.timelinePanel.layerLookup[key].clientSideFilter: null,
                                        listeners: {
                                            'change': function(filter, field) {
                                                if (field.isValid()) {
                                                    this.timelinePanel.applyFilter(record, filter, Ext.getCmp('gxp_timemenufilter').applyFilter.getValue());
                                                }
                                            },
                                            scope: this
                                        },
                                        attributesComboConfig: {
                                            getListParent: function() {
                                                return this.el.up('.x-menu');
                                            }
                                        },
                                        comparisonComboConfig: {
                                            getListParent: function() {
                                                return this.el.up('.x-menu');
                                            }
                                        },
                                        fieldLabel: this.filterLabel,
                                        attributes: schema
                                    }]
                                }],
                                height: 30
                            }]
                        }]
                    }),
                    listeners: {
                        checkchange: function(item, checked) {
                            this.timelinePanel.setLayerVisibility(item, checked, record);
                        },
                        scope: this
                    }
                });
                this.add(item);
            }
        }, this);
        
    }
    
});

Ext.reg('gxp_timelinemenu', gxp.menu.TimelineMenu);
