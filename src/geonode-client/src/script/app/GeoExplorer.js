/**
 * Copyright (c) 2009 The Open Planning Project
 */

/**
 * Constructor: GeoExplorer
 * Create a new GeoExplorer application.
 *
 * Parameters:
 * config - {Object} Optional application configuration properties.
 *
 * Valid config properties:
 * map - {Object} Map configuration object.
 * ows - {String} OWS URL
 * alignToGrid - {boolean} if true, align tile requests to the grid enforced by
 *     tile caches such as GeoWebCache or Tilecache
 *
 * Valid map config properties:
 * layers - {Array} A list of layer configuration objects.
 * center - {Array} A two item array with center coordinates.
 * zoom - {Number} An initial zoom level.
 *
 * Valid layer config properties:
 * name - {String} Required WMS layer name.
 * title - {String} Optional title to display for layer.
 */
var GeoExplorer = Ext.extend(Ext.util.Observable, {
    
    /**
     * Property: map
     * {OpenLayers.Map} The application's map.
     */
    map: null,
    
    /**
     * Property: layers
     * {GeoExt.data.LayerStore} A store containing a record for each layer
     *     on the map.
     */
    layers: null,

    /**
     * Property: capabilities
     * {GeoExt.data.WMSCapabilitiesStore} A store containing a record for each
     *     layer on the server.
     */
    capabilities: null,

    /**
     * Property: mapPanel
     * {GeoExt.MapPanel} the MapPanel instance for the main viewport
     */
    mapPanel: null,
    
    /**
     * Property: legendPanel
     * {GeoExt.LegendPanel} the legend for the main viewport's map
     */
    legendPanel: null,
    
    /**
     * Property: toolbar
     * {Ext.Toolbar} the toolbar for the main viewport
     */
    toolbar: null,

    /**
     * Property: alignToGrid
     * whether or not to restrict tile request to tiled mapping service recommendation
     */
    alignToGrid: false,

    /**
     * Property: capGrid
     * {<Ext.Window>} A window which includes a CapabilitiesGrid panel.
     */
    capGrid: null,

    /**
     * Property: popupCache
     * {Object} An object containing references to visible popups so that 
     *     we can insert responses from multiple requests.
     */
    popupCache: null,
    
    /** api: property[layerSources]
     * A :class:`Ext.data.Store` containing one 
     * :class:`GeoExt.data.WMSCapabilitiesStore` for each WMS service in use by
     * the application, along with service-specific metadata like the service 
     * name.
     */
    layerSources: null,

    /**
     * Property: backgroundManager
     * A :class:`GeoExplorer.BackgroundLayerManager` responsible for fetching
     * and configuring the background layers configured for the GeoNode
     */
    backgroundManager: null,

    //public variables for string literals needed for localization
    addLayersButtonText: "UT:Add Layers",
    areaActionText: "UT:Area",
    backgroundContainerText: "UT:Background",
    capGridAddLayersText: "UT:Add Layers",
    capGridDoneText: "UT:Done",
    capGridText: "UT:Available Layers",
    connErrorTitleText: "UT:Connection Error",
    connErrorText: "UT:The server returned an error",
    connErrorDetailsText: "UT:Details...",
    exportDialogMessage: '<p> UT: Your map is ready to be published to the web! </p>' + '<p> Simply copy the following HTML to embed the map in your website: </p>',
    heightLabel: 'UT: Height',
    infoButtonText: "UT:Get Feature Info",
    largeSizeLabel: 'UT:Large',
    layerAdditionLabel: "UT: or add a new server.",
    layerContainerText: "UT:Map Layers",
    layerPropertiesText: 'UT: Layer Properties',
    layerPropertiesTipText: 'UT: Change layer metadata, format and style',
    layerSelectionLabel: "UT:View available data from:",
    layersContainerText: "UT:Data",
    layersPanelText: "UT:Layers",
    legendPanelText: "UT:Legend",
    lengthActionText: "UT:Length",
    mapSizeLabel: 'UT: Map Size', 
    measureSplitText: "UT:Measure",
    metaDataHeader: 'UT:About this Map',
    metaDataMapAbstract: 'UT:Abstract',
    metaDataMapContact: 'UT:Contact',
    metaDataMapId: "UT:Permalink",
    metaDataMapTitle: 'UT:Title',
    miniSizeLabel: 'UT: Mini',
    navActionTipText: "UT:Pan Map",
    navNextAction: "UT:Zoom to Next Extent",
    navPreviousActionText: "UT:Zoom to Previous Extent",
    noPermalinkText: "UT: This map has not yet been saved.",
    permalinkLabel: 'UT: Permalink',
    premiumSizeLabel: 'UT: Premium',
    printTipText: "UT:Print Map",
    printWindowTitleText: "UT:Print Preview",
    propertiesText: "UT:Properties",
    publishActionText: 'UT:Publish Map',
    removeLayerActionText: "UT:Remove Layer",
    removeLayerActionTipText: "UT:Remove Layer",
    saveFailMessage: "UT: Sorry, your map could not be saved.",
    saveFailTitle: "UT: Error While Saving",
    saveMapText: "UT: Save Map",
    smallSizeLabel: 'UT: Small',
    sourceLoadFailureMessage: 'UT: Error contacting server.\n Please check the url and try again.',
    switchTo3DActionText: "UT:Switch to Google Earth 3D Viewer",
    unknownMapMessage: 'UT: The map that you are trying to load does not exist.  Creating a new map instead.',
    unknownMapTitle: 'UT: Unknown Map',
    unsupportedLayersTitleText: 'UT:Unsupported Layers',
    unsupportedLayersText: 'UT:The following layers cannot be printed:',
    widthLabel: 'UT: Width',
    zoomInActionText: "UT:Zoom In",
    zoomOutActionText: "UT:Zoom Out",
    zoomSelectorText: 'UT:Zoom level',
    zoomSliderTipText: "UT: Zoom Level",
    zoomToLayerExtentText: "UT:Zoom to Layer Extent",
    zoomVisibleButtonText: "UT:Zoom to Visible Extent",

    constructor: function(config) {
        var query = Ext.urlDecode(document.location.search.substr(1));
        var queryConfig = Ext.util.JSON.decode(query.q);
        
        this.initialConfig = Ext.apply({}, queryConfig, config);
        Ext.apply(this, this.initialConfig);

        // add any custom application events
        this.addEvents([
            /**
             * Event: ready
             * Fires when application is ready for user interaction.
             */
            "ready",

            /**
             * Event: idchange
             * Fires upon a new ID provided for the map configuration being edited by this viewer.
             */
            "idchange"
        ]);
        
        // global request proxy and error handling
        Ext.util.Observable.observeClass(Ext.data.Connection);
        Ext.data.Connection.on({
            "beforerequest": function(conn, options) {
                if(this.proxy && options.url.indexOf(this.proxy) !== 0) {
                    var url = Ext.urlAppend(options.url,
                        Ext.urlEncode(options.params));
                    delete options.params;
                    options.url = this.proxy + encodeURIComponent(url);
                }
            },
            "requestexception": function(conn, response, options) {
                if(options.failure) {
                    // exceptions are handled elsewhere
                    return;
                }
                Ext.Msg.show({
                    title: this.connErrorTitleText,
                    msg: this.connErrorText +
                        ": " + response.status + " " + response.statusText,
                    icon: Ext.MessageBox.ERROR,
                    buttons: {ok: this.connErrorDetailsText, cancel: true},
                    fn: function(result) {
                        if(result == "ok") {
                            var details = new Ext.Window({
                                title: response.status + " " + response.statusText,
                                width: 400,
                                height: 300,
                                items: {
                                    xtype: "container",
                                    cls: "error-details",
                                    html: response.responseText
                                },
                                autoScroll: true,
                                buttons: [{
                                    text: "OK",
                                    handler: function() {details.close()}
                                }]
                            });
                            details.show();
                            this.close();
                        }
                    }
                });
            },
            scope: this
        });
        
        // pass on any proxy config to OpenLayers
        if(this.proxy) {
            OpenLayers.ProxyHost = this.proxy;
        }
        
        this.popupCache = {};
        this.backgroundManager = new GeoExplorer.BackgroundLayerManager({
            proxy: this.proxy,
            backgroundLayers: this.backgroundLayers
        });

        this.load();        
    },
    

    /**
     * Method: load
     * Called at the end of construction.  This initiates the sequence that
     *     prepares the application for use.
     */
    load: function() {
        this.layerSources = new Ext.data.SimpleStore({
            fields: ["identifier", "name", "store", "url"],
            data: []
        });

        var dispatchQueue = [
            // create layout as soon as Ext says ready
            function(done) {
                Ext.onReady(function() {
                    this.createLayout();
                    done();
                }, this);
            }
        ];

        for (var id in this.wms) {
            // Load capabilities for each wms passed through the configuration.
            dispatchQueue.push(
                (function(id) {
                    // Create a new scope for 'id'.
                    return function(done){
                        this.addSource(this.wms[id], id, done, done);
                    }; 
                })(id)
            );
        }

        dispatchQueue = dispatchQueue.concat(
            this.backgroundManager.getBackgroundLoaders()
        );

        gxp.util.dispatch(dispatchQueue, this.activate, this);
    },

    /** private: method[addSource]
     * Add a new WMS server to GeoExplorer. The id parameter is optional,
     * and will be given a default if not specified; success and fail 
     * are also optional, and scope only applies if success or fail
     * is passed in.
     */
    addSource: function(url, id, success, fail, scope) {
        scope = scope || this;
        success = OpenLayers.Function.bind(success, scope);
        fail = OpenLayers.Function.bind(fail, scope);

        id = id || OpenLayers.Util.createUniqueID("source");
        var capsURL = this.createWMSCapabilitiesURL(url);
        var store = new GeoExt.data.WMSCapabilitiesStore();

        OpenLayers.Request.GET({
            proxy: this.proxy,
            url: capsURL,
            success: function(request){
                var store = new GeoExt.data.WMSCapabilitiesStore({
                    fields: [
                        {name: "name", type: "string"},
                        {name: "abstract", type: "string"},
                        {name: "queryable", type: "boolean"},
                        {name: "formats"},
                        {name: "styles"},
                        {name: "bbox"},
                        {name: "llbbox"},
                        {name: "minScale"},
                        {name: "maxScale"},
                        {name: "prefix"},
                        {name: "attribution"},
                        {name: "keywords"},
                        {name: "metadataURLs"},
                        // Added for GeoExplorer.
                        {name: "owsType"},
                        {name: "group", type: "string"},
                        {name: "source_id", type: "string"}
                    ]
                });

                store.on("load",function(store){this.describeLayers(store, url, record, success);},this);
                
                var xml = request.responseXML;
                var data = (xml && xml.documentElement) ?
                    xml : request.responseText;
                var format = new OpenLayers.Format.WMSCapabilities();
                var extractedData = format.read(data);
                    
                
                // MODERATELY LARGE DIRTY HACK!
                // Tell each layer where it came from.
                store.on("load",function(store){
                    store.each(function(record) {
                        record.set("source_id", id);
                    }, this);
                });
                               
                var record = new this.layerSources.recordType({
                    url: url,
                    store: store,
                    identifier: id,
                    name: (extractedData.service &&
                        extractedData.service.title) || id
                });
                
                this.layerSources.add(record);                              
 
                try {
                    // Read the response. It's important to note that the
                    // WMSCapabilitiesStore reads the data as well, though
                    // we need to do it ourselves in order to maintain
                    // low coupling.
                    store.loadData(data);
                } catch(err) {
                    OpenLayers.Console.error("Could not load source: " + url);
                    fail();
                    return;
                } 
            },
            failure: function(){
                OpenLayers.Console.error("Couldn't get capabilities document for wms '" + id + "'.");
                fail();
            },
            scope: this
        });
    },

    //provides the records in a capabilities store with fields from a WMS DescribeLayers
    // request and then calls the 'success' callback
    describeLayers : function(store, url, sourceRecord, success) {

        var layerNames = [];
        store.each(function(layer){
            if(layer.get("queryable")){
                layerNames.push(layer.get("name"));
            }
        });
        layerNames = layerNames.join(",");
        
        //TODO: Shouldn't send this request if there are now layers for the request.

        OpenLayers.Request.GET({
            proxy: this.proxy,
            url: this.createOWSUrl(url, {
                SERVICE : "WMS",
                REQUEST: "DescribeLayer",
                VERSION: "1.1.1",
                //ideally this would go in the params option of the
                //load() call below, but the parameter doesn't get encoded
                //properly with a proxied URL
                layers: layerNames
            }),
            success: function(request){

                var describeLayerStore = new GeoExt.data.WMSDescribeLayerStore();
                
                var annotateLayers = function(describeLayerStore){

                    describeLayerStore.each(function(description){
                        var layer = store.getAt(
                            store.find("name", description.get("typeName")));
                        layer.set("owsType", description.get("owsType"));
                    }, this);
                    
                    //final call to done() for the dispatch() method
                    success(sourceRecord);
                };
                
                describeLayerStore.on("load",annotateLayers, this);
                
                
                // var format = new OpenLayers.Format.WMSDescribeLayer();
                // var extractedData = format.read(data);
                
                var xml = request.responseXML;
                var data = (xml && xml.documentElement) ?
                    xml : request.responseText;
                
                describeLayerStore.loadData(data);
            }
        });  
    },
    
    /** private: method[createWMSCapabilitiesURL]
     * Given the URL to an OWS service endpoint, generate a GET request URL for
     * the service's WMS capabilities.
     */
    createWMSCapabilitiesURL: function(url) {
        return url.toLowerCase().indexOf("getcapabilities") == -1 ?
            this.createOWSUrl(url, {
                SERVICE: 'WMS', 
                REQUEST: 'GetCapabilities'
            }) : url;
    },

    createOWSUrl: function(url, params) {
        var argIndex = url.indexOf("?");
        if(argIndex > -1) {
            var search = url.substring(url.indexOf("?")+1);
            url = url.replace(search, Ext.urlEncode(Ext.apply(
                Ext.urlDecode(search), params)));
        } else {
            url = url + "?" + Ext.urlEncode(params);
        }

        return url;
    },

    /**
     * Method: createLayout
     * Create the various parts that compose the layout.
     */
    createLayout: function() {
        
        // create the map
        // TODO: check this.initialConfig.map for any map options
        this.map = new OpenLayers.Map({
            allOverlays: true,
            projection: new OpenLayers.Projection("EPSG:900913"),
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            units: "m",
            maxResolution: 156543.0339,
            maxExtent: new OpenLayers.Bounds(
                -20037508.34, -20037508.34,
                 20037508.34,  20037508.34
            ),
            controls: [
                new OpenLayers.Control.Navigation(),
                new OpenLayers.Control.PanPanel(),
                new OpenLayers.Control.ZoomPanel(),
                new OpenLayers.Control.Attribution()
            ]
        });

        //** Remove this code when OpenLayers #2069 is closed **
        var onDoubleClick = function(ctrl, evt) { 
 	        OpenLayers.Event.stop(evt ? evt : window.event); 
        };
        var controls = this.map.controls[1].controls;
        for(var i = 0; i < controls.length; i++){
            OpenLayers.Event.observe(controls[i].panel_div, "dblclick",  
                OpenLayers.Function.bind(onDoubleClick, this.map.controls[0], controls[i])); 
        }        
        //******************************************************

        //TODO: make this more configurable
        this.map.events.on({
            "preaddlayer" : function(evt){
                if(evt.layer.mergeNewParams){
                    var maxExtent = evt.layer.maxExtent;
                    if (maxExtent) evt.layer.mergeNewParams({
                        transparent: true,
                        format: "image/png",
                        tiled: true,
                        tilesorigin: [maxExtent.left, maxExtent.bottom]
                    });
                }
            },
            scope : this
        });
        

        // place map in panel
        var mapConfig = this.initialConfig.map || {};
        var center = mapConfig.center && 
            new OpenLayers.LonLat(mapConfig.center[0], mapConfig.center[1]).transform(
                new OpenLayers.Projection("EPSG:4326"),
                new OpenLayers.Projection("EPSG:900913")
            ); 
        this.mapPanel = new GeoExt.MapPanel({
            layout: "anchor",
            border: true,
            map: this.map,
            // TODO: update the OpenLayers.Map constructor to accept an initial center
            center: center,
            // TODO: update the OpenLayers.Map constructor to accept an initial zoom
            zoom: mapConfig.zoom,
            items: [
                new GeoExt.ZoomSlider({
                    vertical: true,
                    height: 100,
                    plugins: new GeoExt.ZoomSliderTip({
                        template: "<div>"+this.zoomSliderTipText+": {zoom}<div>"
                    })
                })
            ]
        });
        this.mapPanel.add(this.createMapOverlay());
        
        // create layer store
        this.layers = this.mapPanel.layers;

        var addLayerButton = new Ext.Button({
		tooltip : this.addLayersButtonText,
            disabled: true,
            iconCls: "icon-addlayers",
            handler : this.showCapabilitiesGrid,
            scope: this
        });
        this.on("ready", function() {addLayerButton.enable();});

        var removeLayerAction = new Ext.Action({
            text: this.removeLayerActionText,
            iconCls: "icon-removelayers",
            disabled: true,
            tooltip: this.removeLayerActionTipText,
            handler: function() {
                var node = layerTree.getSelectionModel().getSelectedNode();
                if(node && node.layer) {
                    var layer = node.layer;
                    var store = node.layerStore;
                    var record = store.getAt(store.findBy(function(record) {
                        return record.get("layer") === layer;
                    }));
                    store.remove(record);
                    removeLayerAction.disable();
                }
            }
        });
        
        var prop;
        var layerPropertiesAction = new Ext.Action({
            text: this.layerPropertiesText,
            iconCls: "icon-layerproperties",
            disabled: true,
            tooltip: this.layerPropertiesTipText,
            handler: function() {
                var node = layerTree.getSelectionModel().getSelectedNode();
                if (node && node.layer) {
                    var layer = node.layer;
                    var store = node.layerStore;
                    var record = store.getAt(store.findBy(function(record){
                        return record.get("layer") === layer;
                    }));
                    if (prop) {
                        prop.close();
                    }
                    prop = new Ext.Window({
                        title: "Properties: " + record.get("title"),
                        width: 250,
                        height: 250,
                        layout: "fit",
                        items: [{
                            xtype: "gx_wmslayerpanel",
                            layerRecord: record,
                            defaults: {
                                style: "padding: 10px"
                            }
                        }]
                    });
                    prop.items.get(0).add(new gxp.WMSStylesDialog({
                        title: "Styles",
                        layerRecord: record,
                        autoScroll: true
                    }));
                    prop.show();
                }
            }
        });

        var updateLayerAction = function(sm, node) {
            // allow removal if more than one non-vector layer
            var count = this.mapPanel.layers.queryBy(function(r) {
                return !(r.get("layer") instanceof OpenLayers.Layer.Vector);
            }).getCount();
            removeLayerAction.setDisabled(count <= 1);
            // allow changing properties for WMS layers with styles in their
            // capabilities doc only
            layerPropertiesAction.setDisabled(
                !(node.layer instanceof OpenLayers.Layer.WMS));
        };

        var bgSubTree = new GeoExt.tree.BaseLayerContainer({
            text: this.backgroundContainerText,
            allowDrag: false,
            layerStore: this.layers, 
            loader: {
                filter: function(record) {
                    return record.get('group') === 'background';
                }
            }
        });

        var fgSubTree = new GeoExt.tree.OverlayLayerContainer({
            text: this.layerContainerText,
            allowDrag: false,
            layerStore: this.layers,
            loader: {
                filter: function(record) {
                    return record.get('group') !== 'background';
                }
            }
        });

        var treeRoot = new Ext.tree.TreeNode({
            allowDrop: false
        });
        treeRoot.appendChild(fgSubTree);
        treeRoot.appendChild(bgSubTree);
        
        var layerTree = new Ext.tree.TreePanel({
            border: false,
            rootVisible: false,
            loader: {
                applyLoader: false
            },
            root: treeRoot,
            enableDD: true,
            selModel: new Ext.tree.DefaultSelectionModel({
                listeners: {
                    beforeselect: updateLayerAction,
                    scope: this
                }
            }),
            listeners: {
                contextmenu: function(node, e) {
                    if(node && node.layer) {
                        node.select();
                        var c = node.getOwnerTree().contextMenu;
                        c.contextNode = node;
                        c.showAt(e.getXY());
                    }
                },
                scope: this
            },
            contextMenu: new Ext.menu.Menu({
                items: [
                    {
                        text: this.zoomToLayerExtentText,
                        iconCls: "icon-zoom-visible",
                        handler: function() {
                            var node = layerTree.getSelectionModel().getSelectedNode();
                            if(node && node.layer) {
                                this.map.zoomToExtent(node.layer.restrictedExtent);
                            }
                        },
                        scope: this
                    },
                    removeLayerAction,
                    layerPropertiesAction
                ]
            })
        });

        var layersContainer = new Ext.Panel({
            autoScroll: true,
            border: false,
            title: this.layersContainerText,
            items: [layerTree],
            tbar: [
                addLayerButton,
                Ext.apply(new Ext.Button(removeLayerAction), {text: ""})
            ]
        });

        this.legendPanel = new GeoExt.LegendPanel({
            title: this.legendPanelText,
            border: false,
            hideMode: "offsets",
            split: true,
            autoScroll: true,
            ascending: false,
            map: this.map,
            defaults: {cls: 'legend-item'}
        });

        var titleField = new Ext.form.TextField({
            width: '95%',
            disabled: true,
            fieldLabel: this.metaDataMapTitle,
            listeners: {
                'change': function(field, newValue, oldValue) {
                    this.about.title = newValue;
                },
                scope: this
            }
        });

        var contactField = new Ext.form.TextField({
            width: '95%',
            disabled: true,
            fieldLabel: this.metaDataMapContact,
            listeners: {
                'change': function(field, newValue, oldValue) {
                    this.about.contact = newValue;
                },
                scope: this
            }
        });

        var abstractField = new Ext.form.TextArea({
            width: '95%',
            disabled: true,
            fieldLabel: this.metaDataMapAbstract,
            listeners: {
                'change': function(field, newValue, oldValue) {
                     this.about["abstract"] = newValue;
                },
                scope: this
            }
        });

        var linkField = new Ext.form.TextField({
            width: '95%',
            disabled: true,
            fieldLabel: this.metaDataMapId,
            listeners: {
                scope: this
            }
        });

        var permalink = function(id) {
            // this should really be a template
            return window.location.protocol + "//" +
                window.location.host +
                "/maps/" + id + ".html"; 
        };

        this.on("idchange", function(id) {
            linkField.setValue(permalink(id));
        }, this);

        var metaDataPanel = new Ext.FormPanel({
            bodyStyle: {padding: "5px"},
            //region: 'north',
            autoScroll: true,
            //collapsed: true,
            collapsible: true,
            labelAlign: "top",
            items: [
                titleField,
                contactField,
                abstractField,
                linkField
            ],
            title: this.metaDataHeader,
            height: 250
        });


        this.on("ready", function(){
            titleField.setValue(this.about.title);
            contactField.setValue(this.about.contact);
            abstractField.setValue(this.about["abstract"]);
            if (!this.mapID) {
                linkField.setValue(this.noPermalinkText);
            } else {
                linkField.setValue(permalink(this.mapID));
            }
            metaDataPanel.enable();
        }, this);

        var layersTabPanel = new Ext.TabPanel({
            border: false,
            deferredRender: false,
            items: [layersContainer, this.legendPanel],
            activeTab: 0
        });

        //needed for Safari
        var layersPanel = new Ext.Panel({
            title: this.layersPanelText,
            layout: "fit",
            items: [layersTabPanel]
        });

        var westPanel = new Ext.Container({
            layout: "accordion",
            layoutConfig: {
                animate:true
            },
            region: "west",
            width: 250,
            split: true,
            collapsible: true,
            collapseMode: "mini",
            activeItem: 1,
            items: [
                metaDataPanel, layersPanel
            ]
        });

        this.toolbar = new Ext.Toolbar({
            disabled: true,
            items: this.createTools()
        });

        this.on("ready", function() {
            // enable only those items that were not specifically disabled
            var disabled = this.toolbar.items.filterBy(function(item) {
                return item.initialConfig && item.initialConfig.disabled;
            });
            this.toolbar.enable();
            disabled.each(function(item) {
                item.disable();
            });
        }, this);
        
        this.googleEarthPanel = new GeoExplorer.GoogleEarthPanel({
            mapPanel: this.mapPanel
        });

        this.googleEarthPanel.on("show", function() {
            addLayerButton.disable();
            removeLayerAction.disable();
            layerTree.getSelectionModel().un(
                "beforeselect", updateLayerAction, this);
        }, this);
        
        this.googleEarthPanel.on("hide", function() {
            addLayerButton.enable();
            removeLayerAction.enable();
            layerTree.getSelectionModel().on(
                "beforeselect", updateLayerAction, this);
        }, this);
        
        this.mapPanelContainer = new Ext.Panel({
            layout: "card", 
            region: "center",
            defaults: {
                // applied to each contained panel
                border:false
            },
            items: [
                this.mapPanel,
                this.googleEarthPanel
            ],
            activeItem: 0
        });

        var header = new Ext.Panel({
            region: "north",
            autoHeight: true
        });

        header.on('render', function() {
            header.getEl().appendChild(Ext.get('app-header'));
        });

        var viewport = new Ext.Viewport({
            layout: "border",
            items: [
                header, 
                {
                    region: "center",
                    xtype: "container",
                    layout: "fit",
                    hideBorders: true,
                    items: {
                        layout: "border",
                        deferredRender: false,
                        tbar: this.toolbar,
                        items: [
                            this.mapPanelContainer,
                            westPanel
                        ]
                    }
                }
            ]
        });    

        Lang.registerLinks();
    },
    
    /**
     * Method: activate
     * Activate the application.  Call after application is configured.
     */
    activate: function() {
        if (this.mapid) {
            this.fireevent('idchange', this.mapid);
        }
        
        // add any layers from config
        this.addLayers();

        // initialize tooltips
        Ext.QuickTips.init();
        
        this.fireEvent("ready");
    },

    /** private: method[addLayers]
     * Construct the layer store to be used with the map (referenced as 
     * :attr:`GeoExplorer.layers`).
     */
    addLayers: function() {
        var mapConfig = this.initialConfig.map;

        if(mapConfig && mapConfig.layers) {
            var records = [];
            
            for(var i = 0; i < mapConfig.layers.length; ++i) {
                var conf = mapConfig.layers[i];
                var index = this.layerSources.find("identifier", conf.wms);
                
                if (index == -1) {
                    continue;
                }
                
                var storeRecord = this.layerSources.getAt(index);
                var store = storeRecord.data.store;

                var id = store.find("name", conf.name);
                
                var record, layer;
                if (id >= 0) {
                    /**
                     * If the same layer is added twice, it will get replaced
                     * unless we give each record a unique id.  In addition, we
                     * need to clone the layer so that the map doesn't assume
                     * the layer has already been added.  Finally, we can't
                     * simply set the record layer to the cloned layer because
                     * record.set compares String(value) to determine equality.
                     * 
                     * TODO: suggest record.clone
                     */
                    Ext.data.Record.AUTO_ID++;
                    record = store.getAt(id).copy(Ext.data.Record.AUTO_ID);
                    layer = record.get("layer").clone();
                    record.data.layer = layer;
                    
                    // set layer max extent from capabilities
                    // TODO: make this SRS independent
                    layer.restrictedExtent = 
                        OpenLayers.Bounds.fromArray(record.get("llbbox"));
                    layer.restrictedExtent.transform(
                        new OpenLayers.Projection("EPSG:4326"),
                        new OpenLayers.Projection("EPSG:900913")
                    );
                    
                    layer.maxExtent = layer.restrictedExtent;

                    // set layer visibility from config
                    layer.visibility = ("visibility" in conf) ? conf.visibility : true;
                    
                    // set layer title from config
                    if (conf.title) {
                        /**
                         * Because the layer title data is duplicated, we have
                         * to set it in both places.  After records have been
                         * added to the store, the store handles this
                         * synchronization.
                         */
                        layer.setName(conf.title);
                        record.set("title", conf.title);
                    }

                    record.set("group", conf.group);
                    
                    // set any other layer configuration
                    // ensures that background layers are on the bottom
                    if(record.get("group") === "background") {
                        records.unshift(record);
                    } else {
                        records.push(record);
                    }
                }

            }
            
            this.layers.add(records);

            // set map center
            if(this.mapPanel.center) {
                // zoom does not have to be defined
                this.map.setCenter(this.mapPanel.center, this.mapPanel.zoom);
            } else if (this.mapPanel.extent) {
                this.map.zoomToExtent(this.mapPanel.extent);
            } else {
                this.map.zoomToMaxExtent();
            }
        }

        this.layers.insert(0, this.backgroundManager.getBackgroundLayers()); 
    },

    /**
     * Method: initCapGrid
     * Constructs a window with a capabilities grid.
     */
    initCapGrid: function(){

        // TODO: Might be nice to subclass some of these things into
        // into their own classes.

        var firstSource = this.layerSources.getAt(0);

        var capGridPanel = new GeoExplorer.CapabilitiesGrid({
            store: firstSource.data.store,
            mapPanel : this.mapPanel,
            expander: new GeoExplorer.CapabilitiesRowExpander({ows: firstSource.get("url")}),
            layout: 'fit',
            region: 'center',
            autoScroll: true,
            alignToGrid: this.alignToGrid,
            listeners: {
                rowdblclick: function(panel, index, evt) {
                    panel.addLayers();
                }
            }
        });

        var sourceComboBox = new Ext.form.ComboBox({
            store: this.layerSources,
            valueField: "identifier",
            displayField: "name",
            triggerAction: "all",
            editable: false,
            allowBlank: false,
            forceSelection: true,
            mode: "local",
            value: firstSource.data.identifier,
            listeners: {
                select: function(combo, record, index) {
                    capGridPanel.reconfigure(record.data.store, capGridPanel.getColumnModel());
                    capGridPanel.expander.ows = record.get("url");
                },
                scope: this
            }
        });

        var capGridToolbar = null;

        if (this.proxy || this.layerSources.getCount() > 1) {
            capGridToolbar = [
                new Ext.Toolbar.TextItem({
                    text: this.layerSelectionLabel
                }),
                sourceComboBox
            ];
        }

        if (this.proxy) {
            capGridToolbar.push(new Ext.Button({
                text: this.layerAdditionLabel, 
                handler: function() {
                    newSourceWindow.show();
                }
            }));
        }

        var newSourceWindow = new GeoExplorer.NewSourceWindow({
            modal: true
        });
        
        newSourceWindow.on("server-added", function(url) {
            newSourceWindow.setLoading();
            
            var success = function(record) {
                // The combo box will automatically update when a new item
                // is added to the layerSources store. Now all we have to
                // do is select it. Note: There's probably a better way to do this, 
                // but there doesn't seem to be another way to get the select event
                // to fire.
                var index = this.layerSources.find("identifier", record.get("identifier"));
                sourceComboBox.onSelect(record, index);
                
                // Close the new source window.
                newSourceWindow.hide();
            };
            
            var failure = function() {
                newSourceWindow.setError(this.sourceLoadFailureMessage);
            };
            
            this.addSource(url, null, success, failure, this);
        }, this);
        
        this.capGrid = new Ext.Window({
            title: this.capGridText,
            closeAction: 'hide',
            layout: 'border',
            height: 300,
            width: 600,
            modal: true,
            items: [
                capGridPanel
            ],
            tbar: capGridToolbar,
            bbar: [
                "->",
                new Ext.Button({
                    text: this.capGridAddLayersText,
                    iconCls: "icon-addlayers",
                    handler: function(){
                        capGridPanel.addLayers();
                    },
                    scope : this
                }),
                new Ext.Button({
                    text: this.capGridDoneText,
                    handler: function() {
                        this.capGrid.hide();
                    },
                    scope: this
                })
            ],
            listeners: {
                hide: function(win){
                    capGridPanel.getSelectionModel().clearSelections();
                }
            }
        });
    },

    /**
     * Method: showCapabilitiesGrid
     * Shows the window with a capabilities grid.
     */
    showCapabilitiesGrid: function() {
        if(!this.capGrid) {
            this.initCapGrid();
        }
        this.capGrid.show();
    },

    /** private: method[createMapOverlay]
     * Builds the :class:`Ext.Panel` containing components to be overlaid on the
     * map, setting up the special configuration for its layout and 
     * map-friendliness.
     */
    createMapOverlay: function() {
        var scaleLinePanel = new Ext.BoxComponent({
            width: 100,
            height: 42,
            autoEl: {
                tag: "div",
                cls: "olControlScaleLine overlay-element overlay-scaleline"
            }
        });

        scaleLinePanel.on('render', function(){
            var scaleLine = new OpenLayers.Control.ScaleLine({
                div: scaleLinePanel.getEl().dom
            });

            this.mapPanel.map.addControl(scaleLine);
            scaleLine.activate();
        }, this);

        var zoomStore = new GeoExt.data.ScaleStore({
            map: this.mapPanel.map
        });

        var zoomSelector = new Ext.form.ComboBox({
            emptyText: 'Zoom level',
            tpl: '<tpl for="."><div class="x-combo-list-item">1 : {[parseInt(values.scale)]}</div></tpl>',
            editable: false,
            triggerAction: 'all',
            mode: 'local',
            store: zoomStore,
            anchor: "100%",
            hideLabel: true
        });

        zoomSelector.on({
            click: function(evt) {
                evt.stopEvent();
            },
            mousedown: function(evt) {
                evt.stopEvent();
            },
            select: function(combo, record, index) {
                this.mapPanel.map.zoomTo(record.data.level);
            },
            scope: this
        })

        var zoomSelectorWrapper = new Ext.Container({
            items: [zoomSelector],
            cls: 'overlay-element overlay-scalechooser',
            layout: "form",
            width: 110
        });

        this.mapPanel.map.events.register('zoomend', this, function() {
            var scale = zoomStore.queryBy(function(record) {
                return this.mapPanel.map.getZoom() == record.data.level;
            }, this);

            if (scale.length > 0) {
                scale = scale.items[0];
                zoomSelector.setValue("1 : " + parseInt(scale.data.scale, 10));
            } else {
                if (!zoomSelector.rendered) {
                    return;
                }
                zoomSelector.clearValue();
            }
        });

        var mapOverlay = new Ext.Panel({
            cls: "map-overlay",
            layout: "hbox",
            autoHeight: true,
            width: 225,
            items: [
                scaleLinePanel,
                zoomSelectorWrapper
            ]
        });


        mapOverlay.on("afterlayout", function(){
            scaleLinePanel.getEl().dom.style.position = 'relative';
            scaleLinePanel.getEl().dom.style.display = 'inline';

            mapOverlay.getEl().on("click", function(x){x.stopEvent();});
            mapOverlay.getEl().on("mousedown", function(x){x.stopEvent();});
        }, this);

        return mapOverlay;
    },

    createTools: function() {
        var toolGroup = "toolGroup";
        
        var printButton = new Ext.Button({
            tooltip: this.printTipText,
            iconCls: "icon-print",
            handler: function() {
                var unsupportedLayers = [];
                var printWindow = new Ext.Window({
                    title: this.printWindowTitleText,
                    modal: true,
                    border: false,
                    resizable: false
                });
                printWindow.add(new GeoExt.ux.PrintPreview({
                    mapTitle: this.about["title"],
                    comment: this.about["abstract"],
                    printMapPanel: {
                        map: {
                            controls: [
                                new OpenLayers.Control.Navigation(),
                                new OpenLayers.Control.PanPanel(),
                                new OpenLayers.Control.ZoomPanel(),
                                new OpenLayers.Control.Attribution()
                            ],
                            eventListeners: {
                                "preaddlayer": function(evt) {
                                    if(evt.layer instanceof OpenLayers.Layer.Google) {
                                        unsupportedLayers.push(evt.layer.name);
                                        return false;
                                    }
                                },
                                scope: this
                            }
                        },
                        items: [{
                            xtype: "gx_zoomslider",
                            vertical: true,
                            height: 100,
                            aggressive: true
                        }]
                    },
                    printProvider: {
                        capabilities: window.printCapabilities,
                        listeners: {
                            "beforeprint": function() {
                                // The print module does not like array params.
                                //TODO Remove when http://trac.geoext.org/ticket/216 is fixed.
                                printWindow.items.get(0).printMapPanel.layers.each(function(l){
                                    var params = l.get("layer").params;
                                    for(var p in params) {
                                        if (params[p] instanceof Array) {
                                            params[p] = params[p].join(",");
                                        }
                                    }
                                })
                            },
                            "print": function() {printWindow.close();}
                        }
                    },
                    includeLegend: true,
                    sourceMap: this.mapPanel,
                    legend: this.legendPanel
                }));
                printWindow.show();
                
                // measure the window content width by it's toolbar
                printWindow.setWidth(0);
                var tb = printWindow.items.get(0).items.get(0);
                var w = 0;
                tb.items.each(function(item){
                    if(item.getEl()) {
                        w += item.getWidth();
                    }
                });
                printWindow.setWidth(
                    Math.max(printWindow.items.get(0).printMapPanel.getWidth(),
                    w + 20));
                printWindow.center();
                
                unsupportedLayers.length &&
                    Ext.Msg.alert(this.unsupportedLayersTitleText, this.unsupportedLayersText +
                        "<ul><li>" + unsupportedLayers.join("</li><li>") + "</li></ul>");

            },
            scope: this
        });

        // create a navigation control
        var navAction = new GeoExt.Action({
            tooltip: this.navActionTipText,
            iconCls: "icon-pan",
            enableToggle: true,
            pressed: true,
            allowDepress: false,
            control: new OpenLayers.Control.Navigation(),
            map: this.map,
            toggleGroup: toolGroup
        });
        
        // create a navigation history control
        var historyControl = new OpenLayers.Control.NavigationHistory();
        this.map.addControl(historyControl);

        // create actions for previous and next
        var navPreviousAction = new GeoExt.Action({
		tooltip: this.navPreviousActionText,
            iconCls: "icon-zoom-previous",
            disabled: true,
            control: historyControl.previous
        });
        
        var navNextAction = new GeoExt.Action({
		tooltip: this.navNextAction,
            iconCls: "icon-zoom-next",
            disabled: true,
            control: historyControl.next
        });
        
        
        // create a get feature info control
        var info = {controls: []};
        var infoButton = new Ext.Button({
		tooltip: this.infoButtonText,
            iconCls: "icon-getfeatureinfo",
            toggleGroup: toolGroup,
            enableToggle: true,
            allowDepress: false,
            toggleHandler: function(button, pressed) {
                for (var i = 0, len = info.controls.length; i < len; i++){
                    if(pressed) {
                        info.controls[i].activate();
                    } else {
                        info.controls[i].deactivate();
                    }
                }
            }
        });

        var updateInfo = function() {
            var queryableLayers = this.mapPanel.layers.queryBy(function(x){
                return x.get("queryable");
            });

            var map = this.mapPanel.map;
            var control;
            for (var i = 0, len = info.controls.length; i < len; i++){
                control = info.controls[i];
                control.deactivate();  // TODO: remove when http://trac.openlayers.org/ticket/2130 is closed
                control.destroy();
            }

            info.controls = [];
            queryableLayers.each(function(x){
                var control = new OpenLayers.Control.WMSGetFeatureInfo({
                    url: x.get("layer").url,
                    queryVisible: true,
                    layers: [x.get("layer")],
                    eventListeners: {
                        getfeatureinfo: function(evt) {
                            this.displayPopup(evt, x.get("title") || x.get("name"));
                        },
                        scope: this
                    }
                });
                map.addControl(control);
                info.controls.push(control);
                if(infoButton.pressed) {
                    control.activate();
                }
            }, this);
        };

        this.mapPanel.layers.on("update", updateInfo, this);
        this.mapPanel.layers.on("add", updateInfo, this);
        this.mapPanel.layers.on("remove", updateInfo, this);

        // create split button for measure controls
        var activeIndex = 0;
        var measureSplit = new Ext.SplitButton({
            iconCls: "icon-measure-length",
            tooltip: this.measureSplitText,
            enableToggle: true,
            toggleGroup: toolGroup, // Ext doesn't respect this, registered with ButtonToggleMgr below
            allowDepress: false, // Ext doesn't respect this, handler deals with it
            handler: function(button, event) {
                // allowDepress should deal with this first condition
                if(!button.pressed) {
                    button.toggle();
                } else {
                    button.menu.items.itemAt(activeIndex).setChecked(true);
                }
            },
            listeners: {
                toggle: function(button, pressed) {
                    // toggleGroup should handle this
                    if(!pressed) {
                        button.menu.items.each(function(i) {
                            i.setChecked(false);
                        });
                    }
                },
                render: function(button) {
                    // toggleGroup should handle this
                    Ext.ButtonToggleMgr.register(button);
                }
            },
            menu: new Ext.menu.Menu({
                items: [
                    new Ext.menu.CheckItem(
                        new GeoExt.Action({
				text: this.lengthActionText,
                            iconCls: "icon-measure-length",
                            map: this.map,
                            toggleGroup: toolGroup,
                            group: toolGroup,
                            allowDepress: false,
                            map: this.map,
                            control: this.createMeasureControl(
                                OpenLayers.Handler.Path, "Length")
                        })),
                    new Ext.menu.CheckItem(
                        new GeoExt.Action({
                            text: this.areaActionText,
                            iconCls: "icon-measure-area",
                            map: this.map,
                            toggleGroup: toolGroup,
                            group: toolGroup,
                            allowDepress: false,
                            map: this.map,
                            control: this.createMeasureControl(
                                OpenLayers.Handler.Polygon, "Area")
                            }))
                  ]})});
        measureSplit.menu.items.each(function(item, index) {
            item.on({checkchange: function(item, checked) {
                measureSplit.toggle(checked);
                if(checked) {
                    activeIndex = index;
                    measureSplit.setIconClass(item.iconCls);
                }
            }});
        });
        
        var enable3DButton = new Ext.Button({
            iconCls:"icon-3D",
            tooltip: this.switchTo3DActionText,
            enableToggle: true,
            toggleHandler: function(button, state) {
                if (state === true) {
                    this.mapPanelContainer.getLayout().setActiveItem(1);
                    this.toolbar.disable();
                    button.enable();
                } else {
                    this.mapPanelContainer.getLayout().setActiveItem(0);
                    this.toolbar.enable();
                }
            },
            scope: this
        });

        var tools = [
		     /*
		       ======== UNSUPPORTED TOOLS ==========
		       
            new Ext.Button({
                text: "GeoExplorer",
                iconCls: "icon-geoexplorer",
                handler: this.displayAppInfo
            }),
            "-",
            new Ext.Button({
                tooltip: "Bookmark",
                handler: this.bookmark,
                scope: this,
                iconCls: "icon-save"
            }),
            "-",
            navAction,
            infoButton,
            measureSplit,
            "-",
		     */
            new Ext.Button({
                tooltip: this.saveMapText,
                handler: this.saveMap,
                scope: this,
                iconCls: "icon-save"
            }),
            window.printCapabilities ? printButton : "",
            new Ext.Button({
                handler: function(){
                    this.map.zoomIn();
                },
                tooltip: this.zoomInActionText,
                iconCls: "icon-zoom-in",
                scope: this
            }),
            new Ext.Button({
		    tooltip: this.zoomOutActionText,
                handler: function(){
                    this.map.zoomOut();
                },
                iconCls: "icon-zoom-out",
                scope: this
            }),
            navPreviousAction,
            navNextAction,
            new Ext.Button({
		    	tooltip: this.zoomVisibleButtonText,
                iconCls: "icon-zoom-visible",
                handler: function() {
                    var extent, layer;
                    for(var i=0, len=this.map.layers.length; i<len; ++i) {
                        layer = this.map.layers[i];
                        if(layer.getVisibility()) {
                            if(extent) {
                                extent.extend(layer.maxExtent);
                            } else {
                                extent = layer.maxExtent.clone();
                            }
                        }
                    }
                    if(extent) {
                        this.map.zoomToExtent(extent);
                    }
                },
                scope: this
            }), new Ext.Action({
                tooltip: this.publishActionText,
                handler: this.makeExportDialog,
                scope: this,
                iconCls: 'icon-export'
            }),
            enable3DButton
        ];

        return tools;
    },

    createMeasureControl: function(handlerType, title) {
        
        var styleMap = new OpenLayers.StyleMap({
            "default": new OpenLayers.Style(null, {
                rules: [new OpenLayers.Rule({
                    symbolizer: {
                        "Point": {
                            pointRadius: 4,
                            graphicName: "square",
                            fillColor: "white",
                            fillOpacity: 1,
                            strokeWidth: 1,
                            strokeOpacity: 1,
                            strokeColor: "#333333"
                        },
                        "Line": {
                            strokeWidth: 3,
                            strokeOpacity: 1,
                            strokeColor: "#666666",
                            strokeDashstyle: "dash"
                        },
                        "Polygon": {
                            strokeWidth: 2,
                            strokeOpacity: 1,
                            strokeColor: "#666666",
                            fillColor: "white",
                            fillOpacity: 0.3
                        }
                    }
                })]
            })
        });

        var cleanup = function() {
            if (measureToolTip) {
                measureToolTip.destroy();
            }   
        };

        var makeString = function(metricData) {
            var metric = metricData.measure;
            var metricUnit = metricData.units;
            
            measureControl.displaySystem = "english";
            
            var englishData = metricData.geometry.CLASS_NAME.indexOf("LineString") > -1 ?
            measureControl.getBestLength(metricData.geometry) :
            measureControl.getBestArea(metricData.geometry);

            var english = englishData[0];
            var englishUnit = englishData[1];
            
            measureControl.displaySystem = "metric";
            var dim = metricData.order == 2 ? 
                '<sup>2</sup>' :
                '';
            
            return metric.toFixed(2) + " " + metricUnit + dim + "<br>" + 
                english.toFixed(2) + " " + englishUnit + dim;
        };
        
        var measureToolTip; 
        var measureControl = new OpenLayers.Control.Measure(handlerType, {
            persist: true,
            handlerOptions: {layerOptions: {styleMap: styleMap}},
            eventListeners: {
                measurepartial: function(event) {
                    cleanup();
                    measureToolTip = new Ext.ToolTip({
                        target: Ext.getBody(),
                        html: makeString(event),
                        title: title,
                        autoHide: false,
                        closable: true,
                        draggable: false,
                        mouseOffset: [0, 0],
                        showDelay: 1,
                        listeners: {hide: cleanup}
                    });
                    if(event.measure > 0) {
                        var px = measureControl.handler.lastUp;
                        var p0 = this.mapPanel.getPosition();
                        measureToolTip.targetXY = [p0[0] + px.x, p0[1] + px.y];
                        measureToolTip.show();
                    }
                },
                measure: function(event) {
                    cleanup();                    
                    measureToolTip = new Ext.ToolTip({
                        target: Ext.getBody(),
                        html: makeString(event),
                        title: title,
                        autoHide: false,
                        closable: true,
                        draggable: false,
                        mouseOffset: [0, 0],
                        showDelay: 1,
                        listeners: {
                            hide: function() {
                                measureControl.cancel();
                                cleanup();
                            }
                        }
                    });
                },
                deactivate: cleanup,
                scope: this
            }
        });

        return measureControl;
    },

    /** private: method[makeExportDialog]
     *
     * Create a dialog providing the HTML snippet to use for embedding the 
     * (persisted) map, etc. 
     */
    makeExportDialog: function() { 
        new ExportWizard({map: this.mapID}).show();
    },

    /**
     * Method: extractConfiguration
     * Returns an object that represents the app's current configuration.
     *
     * Returns:
     *{Object} An object that represents the app's current configuration.
     */ 
    extractConfiguration: function() {
        var center = this.map.getCenter().transform(
            new OpenLayers.Projection("EPSG:900913"),
            new OpenLayers.Projection("EPSG:4326")
        );        
        var config = {
            wms: {},
            map: {
                center: [center.lon, center.lat],
                zoom: this.map.zoom,
                layers: []
            },
            about: Ext.apply({}, this.about)
        };

        this.layerSources.each(function(record) {
            config.wms[record.get("identifier")] = record.get("url");
        });
        
        this.layers.each(function(layerRecord) {
            var layer = layerRecord.get('layer');
            var index = this.layerSources.find("identifier", layerRecord.get("source_id"))
            if (layer.displayInLayerSwitcher && index >= 0) {
                // Get the source of this layer.
                var source = this.layerSources.getAt(index);
                
                if (source === null) {
                    OpenLayers.Console.error("Could not find source for layer '" + layerRecord.get("name") + "'");
                    // Return; error gracefully. (This is debatable.)
                    return;
                }
                
                config.map.layers.push({
                    name: layerRecord.get("name"),
                    title: layerRecord.get("title"),
                    visibility: layer.getVisibility(),
                    group: layerRecord.get("group"),
                    wms: source.get("identifier")
                });
            }
        }, this);
        
        return config;
    },

    saveMap: function() {
        var config = this.extractConfiguration();
        var failure = function(response, options) {
            new Ext.Window({
                title: this.saveFailTitle,
                html: this.saveFailMessage
            }).show();
        };

        Ext.Ajax.request({
            url: this.rest,
            method: 'POST',
            jsonData: config,
            success: function(response, options) {
                var id = response.getResponseHeader("Location");
                // trim whitespace to avoid Safari issue where the trailing newline is included
                id = id.replace(/^\s*/,'');
                id = id.replace(/\s*$/,'');
                id = id.match(/[\d]*$/)[0];
                this.fireEvent("idchange", id);
                this.mapID = id; //id is url, not mapID
            }, 
            failure: failure, 
            scope: this
        });
    }
});