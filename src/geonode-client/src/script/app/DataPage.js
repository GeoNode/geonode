
var DataPage = Ext.extend(Page, {
    
    /**
     * Property: capabilities
     * {GeoExt.data.WMSCapabilitiesStore} A store containing a record for each
     *     layer on the server.
     */
    capabilities: null,
    
    
    /**
     * Property: capGrid
     * {<Ext.Window>} A window which includes a CapabilitiesGrid panel.
     */
    capGrid: null,
    
    dataGridText : "UT:Data",
    mapGridText : "UT:Map",
    dataNameHeaderText : "UT:Name",
    dataTitleHeaderText : "UT:Title",
    dataQueryableHeaderText : "UT:Queryable",
    createMapText : "UT:Create Map",
    openMapText : "UT:Open Map",
    mapTitleLabelText: "UT:Title",
    mapAbstractLabelText: "UT:Abstract",
    ameLabelText: 'UT: AME File',
    scenarioLabelText: 'UT: Scenario',
    countryLabelText: 'UT: Country',
    singularFile: 'UT: File',
    pluralFiles: 'UT: Files',

    constructor: function(config) {
	
	// pass on any proxy config to OpenLayers
	if(this.proxy) {
	    OpenLayers.ProxyHost = this.proxy;
	}

        Page.prototype.constructor.apply(this, arguments);
    },
    
    
    /**
     * Method: load
     * Called at the end of construction.  This initiates the sequence that
     *     prepares the application for use.
     */
    load: function() {
	GeoExplorer.util.dispatch(
	    [
            // create layout as soon as Ext says ready
            function(done) {
                Ext.onReady(function() {
                this.createLayout();
                done();
                }, this);
            },
            // load capabilities immediately
            function(done) {
                this.initCapabilities();
                this.capabilities.load({
                    callback: function(){this.describeLayers(done);},
                    scope: this
                });
            }
	    ],
	    // activate app when the above are both done
	    this.activate, this);
    },
    
    describeLayers: function(done){
        layerNames = [];
        this.capabilities.each(function(layer){
            if(layer.get("queryable")){
                layerNames.push(layer.get("name"));
            }
        });
        layerNames = layerNames.join(",");

        //TODO: Shouldn't send this request if there are now layers for the request.
        
        var describeLayerStore = new GeoExt.data.WMSDescribeLayerStore({
            url: this.owsURL({
                SERVICE : "WMS",
                REQUEST: "DescribeLayer",
                VERSION: "1.1.1",
                //ideally this would go in the params option of the
                //load() call below, but the parameter doesn't get encoded
                //properly with a proxied URL
                layers: layerNames
                
            })
        });
        
        var annotateLayers = function(){
            describeLayerStore.each(function(description){
                var layer = this.capabilities.getAt(this.capabilities.find("name", description.get("typeName")));
                layer.set("owsType", description.get("owsType"));
            }, this);
            
            //final call to done() for the dispatch() method
            done();
        };
        describeLayerStore.load({
            callback: annotateLayers,
            scope: this
        });  
    },
    
    /**
     * Method: initCapabilities
     */
    initCapabilities: function() {        
        var args = {
            SERVICE: "WMS",
            REQUEST: "GetCapabilities"
        };

        var url = this.owsURL(args);
        
        this.capabilities = new GeoExt.data.WMSCapabilitiesStore({
            url: url,
            fields: [
                {name: "name", type: "string"},
                {name: "abstract", type: "string"},
                {name: "queryable", type: "boolean"},
                {name: "formats"},
                {name: "styles"},
                {name: "llbbox"},
                {name: "minScale"},
                {name: "maxScale"},
                {name: "prefix"},
                {name: "attribution"},
                {name: "keywords"},
                {name: "metadataURLs"},
                {name: "owsType"}
            ]
        });
    },

    /**
     * Method: owsURL
     */
    
    owsURL : function(params){
        var argIndex = this.ows.indexOf("?");
        if(argIndex > -1) {
            var search = this.ows.substring(this.ows.indexOf("?")+1);
            var url = this.ows.replace(search, Ext.urlEncode(Ext.apply(
                Ext.urlDecode(search), params)));
        } else {
            url = this.ows + "?" + Ext.urlEncode(params);
        }
        if(this.proxy) {
            url = this.proxy + encodeURIComponent(url);
        }

        return url;
    },
    
    
    
    /**
	 * Method: createLayout
	 * Create the various parts that compose the layout.
	 */
    createLayout: function() {
	// this.populateContent();
	
	// create layer store
	//TODO
	this.layers = new GeoExt.data.LayerStore({});
    },
    
    /**
     * Method: activate
     * Activate the application.  Call after application is configured.
     */
    activate: function() {
	this.initPanel();
        
	// initialize tooltips
	Ext.QuickTips.init();
	
	this.fireEvent("ready");
	
    },
    
    
    /**
     * Method: initCapGrid 
     * Constructs a window with a capabilities grid.
     */
    initPanel: function(){
        var riskExpander = new GeoExplorer.CapabilitiesRowExpander({ows: this.ows});
        var overlayExpander = new GeoExplorer.CapabilitiesRowExpander({ows: this.ows});

        var riskStore = new Ext.data.SimpleStore({
            fields: this.capabilities.fields
        });
        
        this.capabilities.each(function(record) {
            if (record.get("prefix") == "risk") riskStore.add([record]);
        });
	
        var overlayStore = new Ext.data.SimpleStore({
            fields: this.capabilities.fields
        });
        
        this.capabilities.each(function(record) {
            if (record.get("prefix") == "overlay") overlayStore.add([record]);
        });

        var ameStore = new Ext.data.GroupingStore({
            proxy: new Ext.data.HttpProxy({url: this.url + "/www/out.json"}),
            reader: new Ext.data.JsonReader({fields: ['rel_tifs','path','scenario','country']}),
            groupField: 'scenario',
            sortInfo: {field: 'scenario', direction: 'ASC'},
            groupOnSort: true,
            autoLoad: true
        });

        
        var ows = this.ows, ame_link_prefix = this.ame_link_prefix;
        var templateLib = {

            ows : function(){
                return ows;
            },

            expanderContent: function(relTifs){
                if(relTifs.length < 1){
                    return "i18n!! No associated layer files";
                } else {
                    var content = "i18n!! Associated layer files (as GeoTiff): ";

                    var links = [];

                    for(var i = 0; i < relTifs.length; i++){
                        links.push("<a href='"
                                   + this.geoTiffUrl(relTifs[i].replace(".grd",""))
                                   + "'>" 
                                   + relTifs[i].replace(/.*\//, "")
                                   + "</a>");
                    }

                    content = content + links.join(", ");

                    return content;
                }
            },
            
            geoTiffUrl: function(path, values) {
                return ame_link_prefix + "/" + path;
            }
        }
        
        var ameExpander = new Ext.grid.RowExpander({
            tpl: Ext.apply(new Ext.Template('{rel_tifs:this.expanderContent}'),
                           templateLib)
        });

        //TODO: avoid duplication here
        this.riskCapGrid = new Ext.grid.GridPanel({
            renderTo:"risk-layer-browser",	    
            // title: this.dataGridText,
            store: riskStore,
            autoScroll: true,
            height:200,
            alignToGrid: this.alignToGrid,
            plugins: riskExpander,
            cm: new Ext.grid.ColumnModel([
            riskExpander,
                {id: "title", header: this.dataTitleHeaderText, dataIndex: "title", sortable: true},
                {header: this.dataNameHeaderText, dataIndex: "name", width: 180, sortable: true}
            ]),
                viewConfig: {/*forceFit: true,*/ autoFill:true },
                sm: new Ext.grid.RowSelectionModel({singleSelect:true})
        });

        this.overlayCapGrid = new Ext.grid.GridPanel({
            renderTo:"overlay-layer-browser",	    
            // title: this.dataGridText,
            store: overlayStore,
            autoScroll: true,
            height:200,
            alignToGrid: this.alignToGrid,
            plugins: overlayExpander,
            cm: new Ext.grid.ColumnModel([
                overlayExpander,
                {id: "title", header: this.dataTitleHeaderText, dataIndex: "title", sortable: true},
                {header: this.dataNameHeaderText, dataIndex: "name", width: 180, sortable: true}
            ]),
            viewConfig: {/*forceFit: true,*/ autoFill:true },
            sm: new Ext.grid.RowSelectionModel({singleSelect:true})
        });

        this.ameGrid = new Ext.grid.GridPanel({
            renderTo: 'ame-layer-browser',
            store: ameStore,
            plugins: [ameExpander],
            columns: [
                ameExpander,
                {id: 'path', header: this.ameLabelText, dataIndex: 'path', renderer: function (x) {
                    return '<a href="' + ame_link_prefix + '/' + x + '">' + x.replace(/.*\//, '') + '</a';
                }},
                {header: this.scenarioLabelText, dataIndex: 'scenario'},
                {header: this.countryLabelText, dataIndex: 'country'}
            ],
            height: 200,
            view: new Ext.grid.GroupingView({
                forceFit:true,
                // custom grouping text template to display the number of items per group
                groupTextTpl: '{text} ({[values.rs.length]} ' +
                    '{[values.rs.length > 1 ? "' + this.singularFile + 
                    '" : "' + this.pluralFiles +'"]})'
            }),
            viewConfig: {autoFill: true}
        });
    }
});
