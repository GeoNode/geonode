/**
 * Copyright (c) 2008-2012 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * requires ../gxp/src/script/widgets/form/CSWFilterField.js
 */

/** api: (define)
 *  module = gxp
 *  class = CatalogueSearchPanel
 *  base_link = `Ext.Panel <http://extjs.com/deploy/dev/docs/?class=Ext.Panel>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: CatalogueSearchPanel(config)
 *   
 *      Create a panel for searching a CS-W.
 */
gxp.CatalogueSearchPanel = Ext.extend(Ext.Panel, {

    /** private: property[border]
     *  ``Boolean``
     */
    border: false,

    /** api: config[maxRecords]
     *  ``Integer`` The maximum number of records to retrieve in one batch.
     *  Defaults to 10.
     */
    maxRecords: 10,

    /** api: config[map]
     *  ``OpenLayers.Map``
     */
    map: null,

    /** api: config[selectedSource]
     *  ``String`` The key of the catalogue source to use on startup.
     */
    selectedSource: null,

    /** api: config[sources]
     *  ``Object`` The set of catalogue sources for which the user will be
     *  able to query on.
     */
    sources: null,

    /* i18n */
    searchFieldEmptyText: "Search",
    searchButtonText: "Search",
    addTooltip: "Create filter",
    addMapTooltip: "Add to map",
    advancedTitle: "Advanced",
    datatypeLabel: "Data type",
    extentLabel: "Spatial extent",
    categoryLabel: "Category",
    datasourceLabel: "Data source",
    filterLabel: "Filter search by",
    removeSourceTooltip: "Switch back to original source",
    topicCategories: null,
    defaultTopic: "General",

    /* end i18n */

    /** private: method[initComponent]
     *  Initializes the catalogue search panel.
     */
    initComponent: function() {
        this.addEvents(
            /** api: event[addlayer]
             *  Fires when a layer needs to be added to the map.
             *
             *  Listener arguments:
             *
             *  * :class:`gxp.CatalogueSearchPanel` this component
             *  * ``String`` the key of the catalogue source to use
             *  * ``Object`` config object for the WMS layer to create.
             */
            "addlayer"
        );
        this.filters = [];
        var sourceComboData = [];
        for (var key in this.sources) {
            sourceComboData.push([key, this.sources[key].title]);
        }
        if (sourceComboData.length === 1) {
            this.selectedSource = sourceComboData[0][0];
        }
        var filterOptions = [['datatype', 'data type'], ['extent', 'spatial extent'], ['category', 'category']];
        if (sourceComboData.length > 1) {
            filterOptions.push(['csw', 'data source']);
        }
        this.items = [{
            xtype: 'form',
            border: false,
            ref: 'form',
            hideLabels: true,
            autoHeight: true,
            style: "margin-left: 5px; margin-right: 5px; margin-bottom: 5px; margin-top: 5px",
            items: [{
                xtype: "compositefield",
                items: [{
                    xtype: "textfield",
                    emptyText: this.searchFieldEmptyText,
                    ref: "../../search",
                    name: "search",
                    width: 300
                }, {
                    xtype: "button",
                    text: this.searchButtonText,
                    handler: this.performQuery,
                    scope: this
                }]
            }, {
                xtype: "fieldset",
                collapsible: true,
                collapsed: true,
                hideLabels: false,
                title: this.advancedTitle,
                items: [{
                    xtype: 'gxp_cswfilterfield',
                    name: 'datatype',
                    property: 'apiso:Type',
                    comboFieldLabel: this.datatypeLabel,
                    comboStoreData: [
                        ['dataset', 'Dataset'],
                        ['datasetcollection', 'Dataset collection'],
                        ['application', 'Application'],
                        ['service', 'Service']
                    ],
                    target: this
                }, {
                    xtype: 'gxp_cswfilterfield',
                    name: 'extent',
                    property: 'BoundingBox',
                    map: this.map,
                    comboFieldLabel: this.extentLabel,
                    comboStoreData: [
                        ['map', 'spatial extent of the map']
                    ],
                    target: this
                }, {
                    xtype: 'gxp_cswfilterfield',
                    name: 'category',
                    property: 'apiso:TopicCategory',
                    comboFieldLabel: this.categoryLabel,
                    comboStoreData: this.topicCategories ? this.topicCategories :
                        [
                            ['farming', 'Farming'],
                            ['biota', 'Biota'],
                            ['boundaries', 'Boundaries'],
                            ['climatologyMeteorologyAtmosphere', 'Climatology/Meteorology/Atmosphere'],
                            ['economy', 'Economy'],
                            ['elevation', 'Elevation'],
                            ['environment', 'Environment'],
                            ['geoscientificinformation', 'Geoscientific Information'],
                            ['health', 'Health'],
                            ['imageryBaseMapsEarthCover', 'Imagery/Base Maps/Earth Cover'],
                            ['intelligenceMilitary', 'Intelligence/Military'],
                            ['inlandWaters', 'Inland Waters'],
                            ['location', 'Location'],
                            ['oceans', 'Oceans'],
                            ['planningCadastre', 'Planning Cadastre'],
                            ['society', 'Society'],
                            ['structure', 'Structure'],
                            ['transportation', 'Transportation'],
                            ['utilitiesCommunications', 'Utilities/Communications']
                        ],
                    target: this
                }, {
                    xtype: "compositefield",
                    id: "csw",
                    ref: "../../cswCompositeField",
                    hidden: true,
                    items: [{
                        xtype: "combo",
                        ref: "../../../sourceCombo",
                        fieldLabel: this.datasourceLabel,
                        store: new Ext.data.ArrayStore({
                            fields: ['id', 'value'],
                            data: sourceComboData
                        }),
                        displayField: 'value',
                        valueField: 'id',
                        mode: 'local',
                        listeners: {
                            'select': function(cmb, record) {
                                this.setSource(cmb.getValue());
                            },
                            'render': function() { 
                                this.sourceCombo.setValue(this.selectedSource);
                            },
                            scope: this
                        },
                        triggerAction: 'all'
                    }, {
                        xtype: 'button',
                        iconCls: 'gxp-icon-removelayers',
                        tooltip: this.removeSourceTooltip,
                        handler: function(btn) {
                            this.setSource(this.initialConfig.selectedSource);
                            this.sourceCombo.setValue(this.initialConfig.selectedSource);
                            this.cswCompositeField.hide();
                        },
                        scope: this
                    }]
                }, {
                    xtype: 'compositefield',
                    items: [{
                        xtype: "combo",
                        fieldLabel: this.filterLabel,
                        store: new Ext.data.ArrayStore({
                            fields: ['id', 'value'],
                            data: filterOptions
                        }),
                        displayField: 'value',
                        valueField: 'id',
                        mode: 'local',
                        triggerAction: 'all'
                    }, {
                        xtype: 'button',
                        iconCls: 'gxp-icon-addlayers',
                        tooltip: this.addTooltip,
                        handler: function(btn) {
                            btn.ownerCt.items.each(function(item) {
                                if (item.getXType() === "combo") {
                                    var id = item.getValue();
                                    this.form.getForm().findField(id).show();
                                }
                            }, this);
                        },
                        scope: this
                    }]
                }]
            }]
        }, {
            xtype: "grid",
            border: false,
            ref: "grid",
            bbar: new Ext.PagingToolbar({
                paramNames: {
                    start: 'startPosition', 
                    limit: 'maxRecords'
                },
                store: this.sources[this.selectedSource].store,
                pageSize: this.maxRecords
            }),
            loadMask: true,
            hideHeaders: true,
            store: this.sources[this.selectedSource].store,
            columns: [{
                id: 'title', 
                xtype: "templatecolumn", 
                tpl: new Ext.XTemplate('<b>{title}</b><br/>{abstract}'), 
                sortable: true
            }, {
                xtype: "actioncolumn",
                width: 30,
                items: [{
                    iconCls: "gxp-icon-addlayers",
                    tooltip: this.addMapTooltip,
                    handler: function(grid, rowIndex, colIndex) {
                        var rec = this.grid.store.getAt(rowIndex);
                        this.addLayer(rec);
                    },
                    scope: this
                }]
            }],
            autoExpandColumn: 'title',
            width: 400,
            height: 300
        }];
        gxp.CatalogueSearchPanel.superclass.initComponent.apply(this, arguments);
    },

    /** private: method[destroy]
     *  Clean up.
     */
    destroy: function() {
        this.sources = null;
        this.map = null;
        gxp.CatalogueSearchPanel.superclass.destroy.call(this);
    },

    /** private: method[setSource]
     *  :arg key: ``String`` The key of the source to search on.
     *
     *  Change the CS-W this panel will search on.
     */
    setSource: function(key) {
        this.selectedSource = key;
        var store = this.sources[key].store;
        this.grid.reconfigure(store, this.grid.getColumnModel());
        this.grid.getBottomToolbar().bindStore(store);
    },

    /** private: method[performQuery]
     *  Query the CS-W and show the results.
     */
    performQuery: function() {
        var store = this.grid.store;
        var searchValue = this.search.getValue();
        var filter = undefined;
        if (searchValue !== "") {
            filter = new OpenLayers.Filter.Comparison({
                type: OpenLayers.Filter.Comparison.LIKE,
                matchCase: false,
                property: 'csw:AnyText',
                value: '*' + searchValue + '*'
            });
        }
        var data = {
            "resultType": "results",
            "maxRecords": this.maxRecords,
            "Query": {
                "typeNames": "gmd:MD_Metadata",
                "ElementSetName": {
                    "value": "full"
                }
            }
        };
        var fullFilter = this.getFullFilter(filter);
        if (fullFilter !== undefined) {
            Ext.apply(data.Query, {
                "Constraint": {
                    version: "1.1.0",
                    Filter: fullFilter
                }
            });
        }
        // use baseParams so paging takes them into account
        store.baseParams = data;
        store.load();
    },

    /** private: method[getFullFilter]
     *  :arg filter: ``OpenLayers.Filter`` The filter to add to the other existing 
     *  filters. This is normally the free text search filter.
     *  :returns: ``OpenLayers.Filter`` The combined filter.
     *
     *  Get the filter to use in the CS-W query.
     */
    getFullFilter: function(filter) {
        var filters = [];
        if (filter !== undefined) {
            filters.push(filter);
        }
        filters = filters.concat(this.filters);
        if (filters.length <= 1) {
            return filters[0];
        } else {
            return new OpenLayers.Filter.Logical({
                type: OpenLayers.Filter.Logical.AND,
                filters: filters
            });
        }
    },

    /** private: method[addFilter]
     *  :arg filter: ``OpenLayers.Filter`` The filter to add.
     *
     *  Add the filter to the list of filters to use in the CS-W query.
     */
    addFilter: function(filter) {
        this.filters.push(filter);
    },

    /** private: method[removeFilter]
     *  :arg filter: ``OpenLayers.Filter`` The filter to remove.
     *
     *  Remove the filter from the list of filters to use in the CS-W query.
     */
    removeFilter: function(filter) {
        this.filters.remove(filter);
    },

    /** private: method[findWMS]
     *  :arg links: ``Array`` The links to search for a GetMap URL.
     *  :returns: ``Object`` A config object with the url and the layer name.
     *
     *  Look up the WMS url in a set of hyperlinks.
     *  TODO: find a more solid way to do this, without using GetCapabilities
     *  preferably.
     */
    findWMS: function(links) {
        var url = null, name = null;
        for (var i=0, ii=links.length; i<ii; ++i) {
            var link = links[i];
            if (link && link.toLowerCase().indexOf('service=wms') > 0) {
                var obj = OpenLayers.Util.createUrlObject(link);
                url = obj.protocol + "//" + obj.host + ":" + obj.port + obj.pathname.replace("download","geoserver");
                name = obj.args.layers;
                break;
            }
        }
        if (url !== null && name !== null) {
            return {
                url: url,
                name: name
            };
        } else {
            var urlParts = links[0].split('/');
            var name = urlParts[urlParts.length -1];
            return {
                url: links[0],
                name: name
            }
        }
    },

    /** private: method[addLayer]
     *  :arg record: ``GeoExt.data.LayerRecord`` The layer record to add.
     *      
     *  Add a WMS layer coming from a catalogue search.
     */
    addLayer: function(record) {
        var uri = record.get("URI");
        var bounds = record.get("bounds");
        var bLeft = bounds.left,
            bRight = bounds.right,
            bBottom = bounds.bottom,
            bTop = bounds.top;
        var left = Math.min(bLeft, bRight),
            right = Math.max(bLeft, bRight),
            bottom = Math.min(bBottom, bTop),
            top = Math.max(bBottom, bTop);
        var wmsInfo = this.findWMS(uri);
        if (wmsInfo === false) {
            // fallback to dct:references
            var references = record.get("references");
            wmsInfo = this.findWMS(references);
        }
        if (wmsInfo !== false) {
            this.fireEvent("addlayer", this, this.selectedSource, Ext.apply({
                title: record.get('title')[0],
                bbox: [left, bottom, right, top],
                srs: "EPSG:4326",
                subject: this.getCategoryTitle(record)
            }, wmsInfo));
        }
    },


    getCategoryTitle: function(record){
        var subject = this.defaultTopic;
        try {
            subject = record.get("subject")[0];
        } catch (ex) {
            return subject;
        }
        for (var c = 0; c < this.topicCategories.length; c++)
        {
                if (this.topicCategories[c][0] === subject) {
                    return this.topicCategories[c][1];
                }
        }
        return subject;

    }

});

/** api: xtype = gxp_cataloguesearchpanel */
Ext.reg('gxp_cataloguesearchpanel', gxp.CatalogueSearchPanel);
