/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @include widgets/NewSourceWindow.js
 */

/** api: (define)
 *  module = gxp.grid
 *  class = CapabilitiesGrid
 *  base_link = `Ext.grid.GridPanel <http://extjs.com/deploy/dev/docs/?class=Ext.grid.GridPanel>`_
 */
Ext.namespace("gxp.grid");

/** api: constructor
 *  .. class:: CapabilitiesGrid(config)
 *  
 *      Create a new grid displaying the WMS cabilities of a URL, or the
 *      contents of a ``GeoExt.data.WMSCapabilitiesStore``\ .  The user can
 *      add layers to a passed-in ``GeoExt.MapPanel`` from the grid.
 */
gxp.grid.CapabilitiesGrid = Ext.extend(Ext.grid.GridPanel, {

    /** api: config[store]
     *  ``GeoExt.data.LayerStore``
     */
    store: null,

    /** api: config[metaStore]
     * ``Ext.data.Store``
     * A Store containing the alternative stores that are available for this 
     * GridPanel.  Stores added using the grid toolbar's 'add sources' button
     * will be added to this store.
     *
     * The store must provide at least the following fields:
     * 
     * .. list-table::
     *     :widths: 20 80
     * 
     *     * - ``name``
     *       - the display name for the store
     *     * - ``store`` 
     *       - the ``WMSCapabilitiesStore`` instance
     *     * - ``identifier``
     *       - an id string that layers may use to associate themselves with a 
     *         source (useful for serialization)
     *     * - ``url``
     *       - the root URL to the source's OWS service
     */

    /** api: config[cm]
     * ``Ext.grid.ColumnModel`` or Array[Object]
     * The ColumnModel as normally specified in Ext Grids
     */
    cm: null,

    /**
     * api: property[expander]
     * A plugin, such as a :class:'RowExpander', which displays more
     * information about a capability record.
     */
    expander: null,

    /** config: config[mapPanel]
     *  ``GeoExt.MapPanel``
     *  Map panel to which layers can be added via this grid.
     */
    mapPanel : null,

    /** api: config[url]
     *  ``String``
     *  The  OWS URL to which the GetCapabilities request is sent.  Necessary if
     *  a store is not passed in as a configuration option.
     */
    url: null,

    /** api: config[url]
     * The id of the column to auto-expand.  Unlike the standard ExtJS 
     * ``GridPanel``, this class provides a default value of 'title'.
     */
    autoExpandColumn: "title",

    /** api: config[allowNewSources]
     * ``Boolean``
     * Use this property (set it to false) to force the widget to hide the option to add new sources
     * even when a proxy is set up. Defaults to true.
     */
    allowNewSources: true,

    /** api: i18n[keys]
     * - nameHeaderText 
     * - titleHeaderText 
     * - queryableHeaderText 
     * - layerSelectionLabel
     * - layerAdditionLabel
     * - expanderTemplateText
     */
    nameHeaderText : "Name",
    titleHeaderText : "Title",
    queryableHeaderText : "Queryable",
    layerSelectionLabel: "View available data from:",
    layerAdditionLabel: "or add a new server.",
    expanderTemplateText: "<p><b>Abstract:</b> {abstract}</p>",

    /** private: method[constructor]
     */
    constructor: function() {
        this.addEvents(
            /** api: event[sourceselected]
             *  Fired when a new source is selected.
             *
             *  Listener arguments:
             *
             *  * grid - :class:`gxp.grid.CapabilitiesGrid` This grid.
             *  * source - :class:`gxp.plugins.LayerSource` The selected source.
             */
            "sourceselected"
        );
        gxp.grid.CapabilitiesGrid.superclass.constructor.apply(this, arguments);
    },

    /** private: method[initComponent]
     *
     *  Initializes the CapabilitiesGrid. Creates and loads a WMS Capabilities 
     *  store from the url property if one is not passed as a configuration 
     *  option. 
     */
    initComponent: function(){

        if(!this.store){
            this.store = new GeoExt.data.WMSCapabilitiesStore({
                url: this.url + "?service=wms&request=GetCapabilities"
            });

            this.store.load();
        }

        this.on('afterrender', function() {  
            this.fireEvent('sourceselected', this, this.store);
        }, this);

        if (!("expander" in this)){
            this.expander = new Ext.grid.RowExpander({
                tpl : new Ext.Template(this.expanderTemplateText)
            });
        }

        if(!this.plugins && this.expander){
            this.plugins = this.expander;
        }

        if(!this.cm){
            var cm = [
                {id: "title", header: this.titleHeaderText, dataIndex: "title", sortable: true},
                {header: this.nameHeaderText, dataIndex: "name", width: 180, sortable: true},
                {header: this.queryableHeaderText, dataIndex: "queryable", width: 70,
                    renderer: function(value, metaData, record, rowIndex, colIndex, store) {
                        metaData.css = 'x-btn';
                        var css = 'x-btn cancel';
                        if (value) {
                            css = 'x-btn add';
                        }
                        return '<div style="background-repeat: no-repeat; ' +
                            'background-position: 50% 0%; ' +
                            'height: 16px;" ' +
                            'class="' + css + '">&nbsp;</div>';
                    }
                }
            ];
            if (this.expander) {
                cm.unshift(this.expander);
            }
            this.cm = new Ext.grid.ColumnModel(cm);
        }

        if (!('allowNewSources' in this)) {
            this.allowNewSources = !!this.metaStore;
        }

        if (this.allowNewSources || (this.metaStore && this.metaStore.getCount() > 1)) {
            this.sourceComboBox = new Ext.form.ComboBox({
                store: this.metaStore,
                valueField: "identifier",
                displayField: "name",
                triggerAction: "all",
                editable: false,
                allowBlank: false,
                forceSelection: true,
                mode: "local",
                value: this.metaStore.getAt(this.metaStore.findBy(function(record) {
                    return record.get("store") == this.store;
                }, this)).get("identifier"),
                listeners: {
                    select: function(combo, record, index) {
                        this.fireEvent("sourceselected", this, record.data.store);
                        this.reconfigure(record.data.store, this.getColumnModel());
                        if (this.expander) this.expander.ows = record.get("url");
                    },
                    scope: this
                }
            });

            this.metaStore.on("add", function(store, records, index) {
                this.sourceComboBox.onSelect(records[0], index);
            }, this);

            this.tbar = this.tbar || [];
            this.tbar.push("" + this.layerSelectionLabel);
            this.tbar.push(this.sourceComboBox);
        }

        if (this.allowNewSources) {
            var grid = this;
            if (!this.newSourceWindow) {
                this.newSourceWindow = new gxp.NewSourceWindow({
                    modal: true,
                    metaStore: this.metaStore,
                    addSource: function() { 
                        grid.addSource.apply(grid, arguments); 
                    }
                });
            }

            this.tbar.push(new Ext.Button({
                iconCls: "gxp-icon-addserver",
                text: this.layerAdditionLabel,
                handler: function() {
                    this.newSourceWindow.show();
                },
                scope: this
            }));
        }

        gxp.grid.CapabilitiesGrid.superclass.initComponent.call(this);       
    },

    /** api: config[addSource]
     * A callback method that will be called when a url is entered into this 
     * grid's NewLayerWindow. It should expect the following parameters:
     *
     * .. list-table::
     *     :widths: 20 80
     *
     *     * - ``url`` 
     *       - the URL that the user entered
     *     * - ``success`` 
     *       - a callback to call after the successful addition of a source
     *     * - ``failure``
     *       - a callback to call after a failure to add a source
     *     * - ``scope`` 
     *       - the scope in which to run the callbacks
     *
     * If this is not provided, a default implementation will be used.  It is 
     * recommended that client code use handlers for the 'add' event on the 
     * metaStore rather than overriding this method.
     */
    addSource: function(url, success, failure, scope) {
        scope = scope || this;
        var layerStore = new GeoExt.data.WMSCapabilitiesStore({url:url, autoLoad: true});
        this.metaStore.add(new this.metaStore.recordType({
            url: url,
            store: layerStore,
            identifier: url,
            name: url
        }));
        success.apply(scope);
    },

    /** api: method[addLayers]
     * :param: base: a boolean indicating whether or not to make the new layer
     *     a base layer.
     *
     * Adds a layer to the :class:`GeoExt.MapPanel` of this instance.
     */
    addLayers : function(base){
        var sm = this.getSelectionModel();

        //for now just use the first selected record
        //TODO: force single selection (until we allow
        //adding group layers)
        var records = sm.getSelections();

        var record, layer, newRecords = [];
        for(var i = 0; i < records.length; i++){
            Ext.data.Record.AUTO_ID++;
            record = records[i].copy(Ext.data.Record.AUTO_ID);

            /*
             * TODO: deal with srs and maxExtent
             * At this point, we need to think about SRS if we want the layer to
             * have a maxExtent.  For our app, we are dealing with EPSG:4326
             * only.  This will have to be made more generic for apps that use
             * other srs.
             */
            if (this.alignToGrid) {
                layer = record.getLayer().clone();
                layer.maxExtent = new OpenLayers.Bounds(-180, -90, 180, 90);
            } else {
                layer = record.getLayer();
                /**
                 * TODO: The WMSCapabilitiesReader should allow for creation
                 * of layers in different SRS.
                 */
                if (layer instanceof OpenLayers.Layer.WMS) {
                    layer = new OpenLayers.Layer.WMS(
                        layer.name, layer.url,
                        {layers: layer.params["LAYERS"]},
                        {
                            attribution: layer.attribution,
                            maxExtent: OpenLayers.Bounds.fromArray(
                                record.get("llbbox")
                            ).transform(
                                new OpenLayers.Projection("EPSG:4326"),
                                this.mapPanel.map.getProjectionObject()
                            )
                        }
                    );
                }
            }

            record.data["layer"] = layer;
            record.commit(true);
            
            newRecords.push(record);
        }

        /**
         * The new layer records are ready to be added to the store.  The
         * store may contain temporary layers used for drawing at this
         * point (MeasureControl or other).  There are a number of ways
         * to decide where the new records should be inserted.  For the
         * sake of simplicity, lets assume they goes under the first vector
         * layer found.
         */
        if(newRecords.length) {
            var index = this.mapPanel.layers.findBy(function(r) {
                return r.getLayer() instanceof OpenLayers.Layer.Vector;
            });
            if(index !== -1) {
                this.mapPanel.layers.insert(index, newRecords);
            } else {
                this.mapPanel.layers.add(newRecords);
            }
        }
    }
});

/** api: xtype = gxp_capabilitiesgrid */
Ext.reg('gxp_capabilitiesgrid', gxp.grid.CapabilitiesGrid); 
