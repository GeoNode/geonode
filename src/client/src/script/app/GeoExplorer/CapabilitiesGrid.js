/**
 * Copyright (c) 2008 The Open Planning Project
 *
 */

/**
 * @requires GeoExplorer.js
 */

/**
 * api: (define)
 * module = GeoExplorer
 * class = CapabilitiesGrid(config)
 * extends = Ext.grid.GridPanel
 */

/** api: constructor
 * ..class:: CapabilitiesGrid(config)
 * :param: config: A configuration :class:`Object`
 *
 * Create a new grid displaying the WMS cabilities of a URL, or the contents of 
 * a :class:`GeoExt.data.WMSCapabilitiesStore`\ .  The user can add layers to a
 * passed-in :class:`GeoExt.MapPanel` from the grid.
 */

Ext.namespace("GeoExplorer");
GeoExplorer.CapabilitiesGrid = Ext.extend(Ext.grid.GridPanel, {

    store: null,

    cm: null,

    /**
     * api: property[expander]
     * A plugin, such as a :class:'RowExpander', which displays more
     * information about a capability record.
     */
    expander: null,

    /**
     * api: property[mapPanel]
     * A :class:`GeoExt.MapPanel` to which layers can be added via this grid.
     */
    mapPanel : null,

    /** api: property[url]
     * A :class:`String` containing an OWS URL to which the GetCapabilities 
     * request is sent.  Necessary if a store is not passed in as a 
     * configuration option.
     */
    url: null,

    autoExpandColumn: "title",


    nameHeaderText : "UT:Name",
    titleHeaderText : "UT:Title",
    queryableHeaderText : "UT:Queryable",


    /** api: method[initComponent]
     * 
     * Initializes the CapabilitiesGrid. Creates and loads a WMS Capabilities 
     * store from the url property if one is not passed as a configuration 
     * option. 
     */
    initComponent: function(){

        if(!this.store){
            this.store = new GeoExt.data.WMSCapabilitiesStore({
                url: this.url + "?service=wms&request=GetCapabilities"
            });

            this.store.load();
        }

        if(!this.expander){
            this.expander = new Ext.grid.RowExpander({
                tpl : new Ext.Template(
                    '<p><b>Abstract:</b> {abstract}</p>')}); 
        }

        if(!this.plugins){
            this.plugins = this.expander;
        }

        if(!this.cm){
            this.cm = new Ext.grid.ColumnModel([
                this.expander,
                {id: "title", header: this.titleHeaderText, dataIndex: "title", sortable: true},
                {header: this.nameHeaderText, dataIndex: "name", width: 180, sortable: true},
                {header: this.queryableHeaderText, dataIndex: "queryable"}
            ]);
        }

        GeoExplorer.CapabilitiesGrid.superclass.initComponent.call(this);       
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

            layer = record.get("layer").clone();
            record.set("layer", null); //need to do this because record.set compares String(value) to determine equality (dumb)
            record.set("layer", layer);

            /*
             * TODO: deal with srs and maxExtent
             * At this point, we need to think about SRS if we want the layer to
             * have a maxExtent.  For our app, we are dealing with EPSG:4326
             * only.  This will have to be made more generic for apps that use
             * other srs.
             */
            layer.restrictedExtent = OpenLayers.Bounds.fromArray(record.get("llbbox"));

            if (this.alignToGrid) {
                layer.maxExtent = new OpenLayers.Bounds(-180, -90, 180, 90);
            } else {
                layer.maxExtent = layer.restrictedExtent;
            }
            
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
                return r.get("layer") instanceof OpenLayers.Layer.Vector;
            });
            if(index !== -1) {
                this.mapPanel.layers.insert(index, newRecords);
            } else {
                this.mapPanel.layers.add(newRecords);
            }
        }

    }
});
