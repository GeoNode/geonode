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
var GeoExplorer = Ext.extend(gxp.Viewer, {
    
    /**
     * api: config[localGeoServerBaseUrl]
     * ``String`` url of the local GeoServer instance
     */
    
    /**
     * private: property[mapPanel]
     * the :class:`GeoExt.MapPanel` instance for the main viewport
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
    
    /** private: property[describeLayerCache]
     *  ``Object`` Cache of parsed DescribeLayer responses for all WMS layer
     *      sources, keyed by service URL.
     */
    describeLayerCache: null,
    
    /** private: property[busyMask]
     */
    busyMask: null,
    
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
    layerPropertiesTipText: 'UT: Change layer format and style',
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
    saveNotAuthorizedMessage: "UT: You Must be logged in to save this map.",
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
        this.popupCache = {};
        this.describeLayerCache = {};
        // add any custom application events
        this.addEvents([
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
                // use django's /geoserver endpoint when talking to the local
                // GeoServer's RESTconfig API
                var url = options.url.replace(
                    /^(http[s]?:\/\/[^:]*)(:80|:443)?\//, "$1/");
                if(url.indexOf(this.localGeoServerBaseUrl + "rest/") === 0) {
                    options.url = url.replace(new RegExp("^" +
                        this.localGeoServerBaseUrl), "/geoserver/");
                    return;
                };
                // use the proxy for all non-local requests
                if(this.proxy && options.url.indexOf(this.proxy) !== 0 &&
                        options.url.indexOf(window.location.protocol) === 0) {
                    var parts = options.url.replace(/&$/, "").split("?");
                    var params = Ext.apply(parts[1] && Ext.urlDecode(
                        parts[1]) || {}, options.params);
                    var url = Ext.urlAppend(parts[0], Ext.urlEncode(params));
                    delete options.params;
                    options.url = this.proxy + encodeURIComponent(url);
                }
            },
            "requestexception": function(conn, response, options) {
                if(options.failure) {
                    // exceptions are handled elsewhere
               } else {
                    this.busyMask && this.busyMask.hide();
                    this.displayXHRTrouble(response);
                }
            },
            scope: this
        });
        
        // register the color manager with every color field
        Ext.util.Observable.observeClass(gxp.form.ColorField);
        gxp.form.ColorField.on({
            render: function(field) {
                var manager = new Styler.ColorManager();
                manager.register(field);
            }
        });

        // limit combo boxes to the window they belong to - fixes issues with
        // list shadow covering list items
        Ext.form.ComboBox.prototype.getListParent = function() {
            return this.el.up(".x-window") || document.body;
        }
        
        // don't draw window shadows - allows us to use autoHeight: true
        // without using syncShadow on the window
        Ext.Window.prototype.shadow = false;
        
        // set SLD defaults for symbolizer
        OpenLayers.Renderer.defaultSymbolizer = {
            fillColor: "#808080",
            fillOpacity: 1,
            strokeColor: "#000000",
            strokeOpacity: 1,
            strokeWidth: 1,
            strokeDashstyle: "solid",
            pointRadius: 3,
            graphicName: "square",
            haloColor: "#FFFFFF",
            fontColor: "#000000"
        };
        
        GeoExplorer.superclass.constructor.apply(this, arguments);
    },
    
    loadConfig: function(config) {
        var query = Ext.urlDecode(document.location.search.substr(1));
        var queryConfig = Ext.util.JSON.decode(query.q);
        this.configManager = new GeoNode.ConfigManager(
            Ext.apply({}, queryConfig, config));

        GeoExplorer.superclass.loadConfig.apply(this,
            [this.configManager.getViewerConfig()]);
    },
    
    displayXHRTrouble: function(response) {
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
                            handler: function() { details.close(); }
                        }]
                    });
                    details.show();
                    this.close();
                }
            }
        });
    },
    
    addLayerSource: function(options) {
        var source = GeoExplorer.superclass.addLayerSource.apply(this, arguments);
        source instanceof gxp.plugins.WMSSource && source.on("ready", function() {
            var request = source.store.reader.raw.capability.request.describelayer;
            if (!request) {
                return;
            }
            var layers = [];
            source.store.each(function(r) {
                layers.push(r.get("name"));
            });
            Ext.Ajax.request({
                url: source.url,
                params: {
                    "SERVICE": "WMS",
                    "REQUEST": "DescribeLayer",
                    "VERSION": source.store.reader.raw.version,
                    "LAYERS": layers.join(",")
                },
                disableCaching: false,
                success: function(response) {
                    this.describeLayerCache[request.href] =
                        new OpenLayers.Format.WMSDescribeLayer().read(
                            response.responseXML &&
                            response.responseXML.documentElement ?
                                response.responseXML : response.responseText);
                },
                failure: function() {
                    // well, bad luck, but no need to worry
                },
                scope: this
            });
        }, this);
        return source;
    },
    
    initMapPanel: function() {
        this.mapItems = [{
            xtype: "gx_zoomslider",
            vertical: true,
            height: 100,
            plugins: new GeoExt.ZoomSliderTip({
                template: "<div>"+this.zoomSliderTipText+": {zoom}<div>"
            })
        }];
        
        GeoExplorer.superclass.initMapPanel.apply(this, arguments);
        
        this.mapPanel.map.events.register("preaddlayer", this, function(e) {
            e.layer instanceof OpenLayers.Layer.WMS && !e.layer.singleTile &&
                e.layer.maxExtent && e.layer.mergeNewParams({
                    tiled: true,
                    tilesOrigin: [e.layer.maxExtent.left, e.layer.maxExtent.bottom]
                }
            );
        });
    },
    
    /**
     * Method: initPortal
     * Create the various parts that compose the layout.
     */
    initPortal: function() {

        // TODO: make a proper component out of this
        var mapOverlay = this.createMapOverlay();
        this.mapPanel.add(mapOverlay);

        var addLayerButton = new Ext.Button({
            tooltip : this.addLayersButtonText,
            disabled: true,
            iconCls: "icon-addlayers",
            handler : this.showCapabilitiesGrid,
            scope: this
        });
        this.on("ready", function() {addLayerButton.enable();});

        var getRecordFromNode = function(node) {
            if(node && node.layer) {
                var layer = node.layer;
                var store = node.layerStore;
                record = store.getAt(store.findBy(function(r) {
                    return r.get("layer") === layer;
                }));
            }
            return record;
        };

        var getSelectedLayerRecord = function() {
            var node = layerTree.getSelectionModel().getSelectedNode();
            return getRecordFromNode(node);
        };
        
        var removeLayerAction = new Ext.Action({
            text: this.removeLayerActionText,
            iconCls: "icon-removelayers",
            disabled: true,
            tooltip: this.removeLayerActionTipText,
            handler: function() {
                var record = getSelectedLayerRecord();
                if(record) {
                    this.mapPanel.layers.remove(record);
                    removeLayerAction.disable();
                }
            },
            scope: this
        });

        var treeRoot = new Ext.tree.TreeNode({
            text: "Layers",
            expanded: true,
            isTarget: false,
            allowDrop: false
        });
        treeRoot.appendChild(new GeoExt.tree.LayerContainer({
            text: this.layerContainerText,
            iconCls: "gx-folder",
            expanded: true,
            loader: new GeoExt.tree.LayerLoader({
                store: this.mapPanel.layers,
                filter: function(record) {
                    return !record.get("group") &&
                        record.get("layer").displayInLayerSwitcher == true;
                },
                createNode: function(attr) {
                    var layer = attr.layer;
                    var store = attr.layerStore;
                    if (layer && store) {
                        var record = store.getAt(store.findBy(function(r) {
                            return r.get("layer") === layer;
                        }));
                        if (record && !record.get("queryable")) {
                            attr.iconCls = "gx-tree-rasterlayer-icon";
                        }
                    }
                    return GeoExt.tree.LayerLoader.prototype.createNode.apply(this, [attr]);
                }
            }),
            singleClickExpand: true,
            allowDrag: false,
            listeners: {
                append: function(tree, node) {
                    node.expand();
                }
            }
        }));
        
        treeRoot.appendChild(new GeoExt.tree.LayerContainer({
            text: this.backgroundContainerText,
            iconCls: "gx-folder",
            expanded: true,
            group: "background",
            loader: new GeoExt.tree.LayerLoader({
                baseAttrs: {checkedGroup: "background"},
                store: this.mapPanel.layers,
                filter: function(record) {
                    return record.get("group") === "background" &&
                        record.get("layer").displayInLayerSwitcher == true;
                },
                createNode: function(attr) {
                    var layer = attr.layer;
                    var store = attr.layerStore;
                    if (layer && store) {
                        var record = store.getAt(store.findBy(function(r) {
                            return r.get("layer") === layer;
                        }));
                        if (record) {
                            if (!record.get("queryable")) {
                                attr.iconCls = "gx-tree-rasterlayer-icon";
                            }
                            if (record.get("fixed")) {
                                attr.allowDrag = false;
                            }
                        }
                    }
                    return GeoExt.tree.LayerLoader.prototype.createNode.apply(this, arguments);
                }
            }),
            singleClickExpand: true,
            allowDrag: false,
            listeners: {
                append: function(tree, node) {
                    node.expand();
                }
            }
        }));

        var showPropertiesAction = new Ext.Action({
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
                    var backupParams = Ext.apply({}, record.get("layer").params);
                    var prop = new Ext.Window({
                        title: "Properties: " + record.get("layer").name,
                        width: 280,
                        autoHeight: true,
                        items: [{
                            xtype: "gx_wmslayerpanel",
                            autoHeight: true,
                            layerRecord: record,
                            defaults: {
                                style: "padding: 10px;",
                                autoHeight: true,
                                hideMode: "offsets"
                            }
                        }]
                    });
                    // disable the "About" tab's fields to indicate that they
                    // are read-only
                    //TODO WMSLayerPanel should be easier to configure for this
                    prop.items.get(0).items.get(0).cascade(function(i) {
                        i instanceof Ext.form.Field && i.setDisabled(true);
                    });
                    var layerUrl = record.get("layer").url;
                    // configure writer plugin for styles
                    var styleWriter = new gxp.plugins.GeoServerStyleWriter({
                        baseUrl: layerUrl.split(
                            "?").shift().replace(/\/(wms|ows)\/?$/, "/rest")
                    });
                    // get DescribeLayer entry
                    var layerDescription;
                    var cache = this.describeLayerCache[layerUrl];
                    if (cache) {
                        for (var i=0,len=cache.length; i<len; ++i) {
                            if (cache[i].layerName == record.get("name")) {
                                layerDescription = cache[i];
                                break;
                            }
                        }
                    };
                    var stylesDialog;
                    var createStylesDialog = function() {
                        var tabPanel;
                        if(stylesDialog) {
                            tabPanel = prop.items.get(0);
                            tabPanel.remove(stylesDialog.ownerCt);
                            setTab = true;
                        }
                        stylesDialog = new gxp.WMSStylesDialog({
                            style: "padding: 10px;",
                            editable: layer.url.indexOf(
                                this.localGeoServerBaseUrl) === 0,
                            layerRecord: record,
                            layerDescription: layerDescription,
                            plugins: [styleWriter],
                            autoScroll: true,
                            listeners: {
                                "ready": function() {
                                    // we don't want the Cancel and Save buttons
                                    // if we cannot edit styles
                                    stylesDialog.editable === false &&
                                        stylesDialog.ownerCt.getFooterToolbar().hide();
                                },
                                "modified": function() {
                                    // enable the save button
                                    stylesDialog.ownerCt.buttons[1].enable();
                                },
                                "styleselected": function() {
                                    // enable the cancel button
                                    stylesDialog.ownerCt.buttons[0].enable();
                                }
                            }
                        });
                        prop.items.get(0).add({
                            title: "Styles",
                            style: "",
                            autoHeight: true,
                            items: stylesDialog,
                            buttons: [{
                                text: "Cancel",
                                disabled: true,
                                handler: function() {
                                    layer.mergeNewParams({
                                        "STYLES": backupParams.STYLES
                                    });
                                    createStylesDialog.call(this);
                                },
                                scope: this
                            }, {
                                text: "Save",
                                disabled: true,
                                handler: function() {
                                    this.busyMask = new Ext.LoadMask(prop.el,
                                        {msg: "Applying style changes..."});
                                    this.busyMask.show();
                                    var updateLayer = function() {
                                        var rec = stylesDialog.selectedStyle;
                                        layer.mergeNewParams({
                                            "STYLES": rec.get("userStyle").isDefault === true ?
                                                "" : rec.get("name"),
                                            "_dc": Math.random()
                                        });
                                        this.busyMask.hide();
                                        createStylesDialog.call(this);
                                    }
                                    styleWriter.write({
                                        success: updateLayer,
                                        scope: this
                                    });
                                },
                                scope: this
                            }]
                        });
                        tabPanel && tabPanel.setActiveTab(stylesDialog.ownerCt);

                    };
                    createStylesDialog.call(this);
                    // add styles tab
                    prop.show();
                }
            },
            scope: this
        });

        var updateLayerActions = function(sel, node) {
            if(node && node.layer) {
                // allow removal if more than one non-vector layer
                var count = this.mapPanel.layers.queryBy(function(r) {
                    return !(r.get("layer") instanceof OpenLayers.Layer.Vector);
                }).getCount();
                if(count > 1) {
                    removeLayerAction.enable();
                } else {
                    removeLayerAction.disable();
                }
                var record = getRecordFromNode(node);
                if (record.get("properties")) {
                    showPropertiesAction.enable();                    
                } else {
                    showPropertiesAction.disable();
                }
            } else {
                removeLayerAction.disable();
                showPropertiesAction.disable();
            }
        };

        var layerTree = new Ext.tree.TreePanel({
            root: treeRoot,
            rootVisible: false,
            border: false,
            enableDD: true,
            selModel: new Ext.tree.DefaultSelectionModel({
                listeners: {
                    beforeselect: updateLayerActions,
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
                beforemovenode: function(tree, node, oldParent, newParent, index) {
                    // change the group when moving to a new container
                    if(oldParent !== newParent) {
                        var store = newParent.loader.store;
                        var index = store.findBy(function(r) {
                            return r.get("layer") === node.layer;
                        });
                        var record = store.getAt(index);
                        record.set("group", newParent.attributes.group);
                    }
                },                
                scope: this
            },
            contextMenu: new Ext.menu.Menu({
                items: [
                    {
                        text: this.zoomToLayerExtentText,
                        iconCls: "icon-zoom-to",
                        handler: function() {
                            var node = layerTree.getSelectionModel().getSelectedNode();
                            if(node && node.layer) {
                                var map = this.mapPanel.map;
                                var extent = node.layer.restrictedExtent || map.maxExtent;
                                map.zoomToExtent(extent, true);
                            }
                        },
                        scope: this
                    },
                    removeLayerAction,
                    showPropertiesAction
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
                Ext.apply(new Ext.Button(removeLayerAction), {text: ""}),
                Ext.apply(new Ext.Button(showPropertiesAction), {text: ""})
            ]
        });

        this.legendPanel = new GeoExt.LegendPanel({
            title: this.legendPanelText,
            border: false,
            hideMode: "offsets",
            split: true,
            autoScroll: true,
            ascending: false,
            map: this.mapPanel.map,
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


        this.on("ready", function(){
            this.mapID = this.initialConfig.id;
            
            titleField.setValue(this.about.title);
            contactField.setValue(this.about.contact);
            abstractField.setValue(this.about["abstract"]);
            if (!this.mapID) {
                linkField.setValue(this.noPermalinkText);
            } else {
                this.fireEvent('idchange', this.mapID);
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
        var westPanel = new Ext.Panel({
            layout: "fit",
            items: [layersTabPanel],
            region: "west",
            width: 250
        });
/*
        var westPanel = new Ext.Container({
            layout: "accordion",
            layoutConfig: {
                animate:true
            },
            
            split: true,
            collapsible: true,
            collapseMode: "mini",
            activeItem: 1,
            items: [
                metaDataPanel, layersPanel
            ]
        });
*/
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
        
        this.googleEarthPanel = new gxp.GoogleEarthPanel({
            mapPanel: this.mapPanel,
            listeners: {
                "beforeadd": function(record) {
                    return record.get("group") !== "background";
                },
                "show": function() {
                    addLayerButton.disable();
                    removeLayerAction.disable();
                    layerTree.getSelectionModel().un(
                        "beforeselect", updateLayerActions, this);
                },
                "hide": function() {
                    addLayerButton.enable();
                    updateLayerActions();
                    layerTree.getSelectionModel().on(
                        "beforeselect", updateLayerActions, this);
                }
            }
        });
        
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
            autoHeight: true,
            contentEl: "app-header"
        });


        var permalink = function(id) {
            return (new Ext.Template("{protocol}//{host}/maps/{id}")).apply({
                protocol: window.location.protocol,
                host: window.location.host,
                id: id
            }) 
        };

        this.moreInfoPanel = new Ext.Panel({
            layout:"fit",
            items: {html: "<a class='link' href='foo'> More info</a>"}
            //TODO: template
        });-

        this.on("idchange", function(id) {
            this.moreInfoPanel.removeAll();
            this.moreInfoPanel.add({
                html: "<a href='"+permalink(id)+"'> More info</a>" //TODO: template
            });
            this.moreInfoPanel.doLayout();
        }, this);

        var titlePanel = new Ext.Panel({
            region: "north",
            autoHeight: true,
            items: [
                {html: "<h3>" + this.about.title + "</h3>"},
                this.moreInfoPanel
            ]
        });


        Lang.registerLinks();


        this.portalItems = [
            header, {
                region: "center",
                xtype: "container",
                layout: "fit",
                hideBorders: true,
                items: {
                    layout: "border",
                    deferredRender: false,
                    tbar: this.toolbar,
                    items: [
                        titlePanel,
                        this.mapPanelContainer,
                        westPanel
                    ]
                }
            }
        ];

        GeoExplorer.superclass.initPortal.apply(this, arguments);
    },
    
    /**
     * Method: initCapGrid
     * Constructs a window with a capabilities grid.
     */
    initCapGrid: function(){

        var source, data = [];        
        for (var id in this.layerSources) {
            source = this.layerSources[id];
            if (source.store) {
                data.push([id, this.layerSources[id].title || id]);                
            }
        }
        var sources = new Ext.data.ArrayStore({
            fields: ["id", "title"],
            data: data
        });

        var firstSource = this.layerSources[data[0][0]];
        var expander = new GeoExplorer.CapabilitiesRowExpander({
            ows: firstSource.url,
            layerDescriptions: firstSource.store.reader.raw &&
                this.describeLayerCache[firstSource.store.reader.raw.capability.request.describelayer.href]
        });
        
        var addLayers = function() {
            var key = sourceComboBox.getValue();
            var layerStore = this.mapPanel.layers;
            var source = this.layerSources[key];
            var records = capGridPanel.getSelectionModel().getSelections();
            var record;
            for (var i=0, ii=records.length; i<ii; ++i) {
                record = source.createLayerRecord({
                    name: records[i].get("name"),
                    source: key,
                    buffer: 0
                });
                if (record) {
                    if (record.get("group") === "background") {
                        layerStore.insert(0, [record]);
                    } else {
                        layerStore.add([record]);
                    }
                }
            }
        };

        var capGridPanel = new Ext.grid.GridPanel({
            store: firstSource.store,
            layout: 'fit',
            region: 'center',
            autoScroll: true,
            autoExpandColumn: "title",
            plugins: [expander],
            colModel: new Ext.grid.ColumnModel([
                expander,
                {header: "Name", dataIndex: "name", width: 150, sortable: true},
                {id: "title", header: "Title", dataIndex: "title", sortable: true}
            ]),
            listeners: {
                rowdblclick: addLayers,
                scope: this
            }
        });

        var sourceComboBox = new Ext.form.ComboBox({
            store: sources,
            valueField: "id",
            displayField: "title",
            triggerAction: "all",
            editable: false,
            allowBlank: false,
            forceSelection: true,
            mode: "local",
            value: data[0][0],
            listeners: {
                select: function(combo, record, index) {
                    var store = this.layerSources[record.get("id")].store;
                    capGridPanel.reconfigure(store, capGridPanel.getColumnModel());
                    // TODO: remove the following when this Ext issue is addressed
                    // http://www.extjs.com/forum/showthread.php?100345-GridPanel-reconfigure-should-refocus-view-to-correct-scroller-height&p=471843
                    capGridPanel.getView().focusRow(0);
                    expander.ows = this.layerSources[record.get("id")].url;
                    expander.layerDescriptions = store.reader.raw &&
                        this.describeLayerCache[store.reader.raw.capability.request.describelayer.href]
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

        var app = this;
        var newSourceWindow = new gxp.NewSourceWindow({
            modal: true,
            listeners: {
                "server-added": function(url) {
                    newSourceWindow.setLoading();
                    this.addLayerSource({
                        config: {url: url}, // assumes default of gx_wmssource
                        callback: function(id) {
                            // add to combo and select
                            var record = new sources.recordType({
                                id: id,
                                title: this.layerSources[id].title || "Untitled" // TODO: titles
                            });
                            sources.insert(0, [record]);
                            sourceComboBox.onSelect(record, 0);
                            newSourceWindow.hide();
                        },
                        failure: function() {
                            // TODO: wire up success/failure
                            newSourceWindow.setError("Error contacting server.\nPlease check the url and try again.");
                        },
                        scope: this
                    });
                },
                scope: this
            },
            // hack to get the busy mask so we can close it in case of a
            // communication failure
            addSource: function(url, success, failure, scope) {
                app.busyMask = scope.loadMask;
            }
        });
        
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
                    handler: addLayers,
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
            autoEl: {
                tag: "div",
                cls: "olControlScaleLine overlay-element overlay-scaleline"
            }
        });

        scaleLinePanel.on('render', function(){
            var scaleLine = new OpenLayers.Control.ScaleLine({
                div: scaleLinePanel.getEl().dom,
                geodesic: true
            });

            this.mapPanel.map.addControl(scaleLine);
            scaleLine.activate();
        }, this);

        var zoomSelectorWrapper = new Ext.Panel({
            cls: 'overlay-element overlay-scalechooser',
            border: false 
        });

        this.on("ready", function() {
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
                width: 110
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
            });
            
            function setScale() {
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
            };
            setScale.call(this);
            this.mapPanel.map.events.register('zoomend', this, setScale);

            zoomSelectorWrapper.add(zoomSelector);
            zoomSelectorWrapper.doLayout();
        }, this);

        var mapOverlay = new Ext.Panel({
            // title: "Overlay",
            cls: 'map-overlay',
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
            map: this.mapPanel.map,
            toggleGroup: toolGroup
        });
        
        // create a navigation history control
        var historyControl = new OpenLayers.Control.NavigationHistory();
        this.mapPanel.map.addControl(historyControl);

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
                            map: this.mapPanel.map,
                            toggleGroup: toolGroup,
                            group: toolGroup,
                            allowDepress: false,
                            map: this.mapPanel.map,
                            control: this.createMeasureControl(
                                OpenLayers.Handler.Path, "Length")
                        })),
                    new Ext.menu.CheckItem(
                        new GeoExt.Action({
                            text: this.areaActionText,
                            iconCls: "icon-measure-area",
                            map: this.mapPanel.map,
                            toggleGroup: toolGroup,
                            group: toolGroup,
                            allowDepress: false,
                            map: this.mapPanel.map,
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
            new Ext.Button({
                tooltip: this.saveMapText,
                handler: this.save,
                scope: this,
                iconCls: "icon-save"
            }),
            new Ext.Action({
                tooltip: this.publishActionText,
                handler: this.makeExportDialog,
                scope: this,
                iconCls: 'icon-export'
            }),
            window.printCapabilities ? printButton : "",
            "-",
            new Ext.Button({
                handler: function(){
                    this.mapPanel.map.zoomIn();
                },
                tooltip: this.zoomInActionText,
                iconCls: "icon-zoom-in",
                scope: this
            }),
            new Ext.Button({
		    tooltip: this.zoomOutActionText,
                handler: function(){
                    this.mapPanel.map.zoomOut();
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
                        this.mapPanel.map.zoomToExtent(extent);
                    }
                },
                scope: this
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

    updateURL: function() {
        /* PUT to this url to update an existing map */
        return this.rest + this.mapID + '/data';
    },

    save: function() {
        var config = this.configManager.getConfig(this);
        
        var failure = function(response, options) {
            var failureMessage = this.saveFailMessage;
            if (response.status == 401) {
                failureMessage = this.saveNotAuthorizedMessage;
            }
            new Ext.Window({
                title: this.saveFailTitle,
                style: "padding: 5px;",
                html: failureMessage
            }).show();
        };

        if (!this.mapID) {
            /* create a new map */ 
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
                    this.mapID = id; //id is url, not mapID
                    this.fireEvent("idchange", id);
                }, 
                failure: failure, 
                scope: this
            });
        }
        else {
            /* save an existing map */
            Ext.Ajax.request({
                url: this.updateURL(),
                method: 'PUT',
                jsonData: config,
                success: function(response, options) {
                    /* nothing for now */
                }, 
                failure: failure, 
                scope: this
            });         
        }
    }
});
