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
    localGeoServerBaseUrl: "",
    
    /**
     * api: config[fromLayer]
     * ``Boolean`` true if map view was loaded with layer parameters
     */
    fromLayer: false,

    /**
     * private: property[mapPanel]
     * the :class:`GeoExt.MapPanel` instance for the main viewport
     */
    mapPanel: null,

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
     * Property: modified
     * ``Number``
     */
    modified: 0,

    /**
     * Property: popupCache
     * {Object} An object containing references to visible popups so that 
     *     we can insert responses from multiple requests.
     */
    popupCache: null,
    
    /** private: property[urlPortRegEx]
     *  ``RegExp``
     */
    urlPortRegEx: /^(http[s]?:\/\/[^:]*)(:80|:443)?\//,
    
    //public variables for string literals needed for localization
    backgroundContainerText: "UT:Background",
    connErrorTitleText: "UT:Connection Error",
    connErrorText: "UT:The server returned an error",
    connErrorDetailsText: "UT:Details...",
    heightLabel: 'UT: Height',
    largeSizeLabel: 'UT:Large',
    layerContainerText: "UT:Map Layers",
    layerSelectionLabel: "UT:View available data from:",
    layersContainerText: "UT:Data",
    layersPanelText: "UT:Layers",
    legendPanelText: "UT:Legend",
    mapSizeLabel: 'UT: Map Size', 
    metadataFormCancelText : "UT:Cancel",
    metadataFormSaveAsCopyText : "UT:Save as Copy",
    metadataFormSaveText : "UT:Save",
    metaDataHeader: 'UT:About this Map',
    metaDataMapAbstract: 'UT:Abstract',
    metaDataMapTitle: 'UT:Title',
    miniSizeLabel: 'UT: Mini',
    premiumSizeLabel: 'UT: Premium',
    propertiesText: "UT:Properties",
    publishActionText: 'UT:Publish Map',
    saveFailMessage: "UT: Sorry, your map could not be saved.",
    saveFailTitle: "UT: Error While Saving",
    saveMapText: "UT: Save Map",
    saveMapAsText: "UT: Save Map As",
    saveNotAuthorizedMessage: "UT: You Must be logged in to save this map.",
    smallSizeLabel: 'UT: Small',
    sourceLoadFailureMessage: 'UT: Error contacting server.\n Please check the url and try again.',
    switchTo3DActionText: "UT:Switch to Google Earth 3D Viewer",
    unknownMapMessage: 'UT: The map that you are trying to load does not exist.  Creating a new map instead.',
    unknownMapTitle: 'UT: Unknown Map',
    widthLabel: 'UT: Width',
    zoomSelectorText: 'UT:Zoom level',
    zoomSliderTipText: "UT: Zoom Level",
    zoomToLayerExtentText: "UT:Zoom to Layer Extent",

    constructor: function(config) {
        this.popupCache = {};
        // add any custom application events
        this.addEvents(
            /**
             * api: event[saved]
             * Fires when the map has been saved.
             *  Listener arguments:
             *  * ``String`` the map id
             */
            "saved",
            /**
             * api: event[beforeunload]
             * Fires before the page unloads. Return false to stop the page
             * from unloading.
             */
            "beforeunload"
        );

        // add old ptypes
        Ext.preg("gx_wmssource", gxp.plugins.WMSSource);
        Ext.preg("gx_olsource", gxp.plugins.OLSource);
        Ext.preg("gx_googlesource", gxp.plugins.GoogleSource);
        
        // global request proxy and error handling
        Ext.util.Observable.observeClass(Ext.data.Connection);
        Ext.data.Connection.on({
            "beforerequest": function(conn, options) {
                // use django's /geoserver endpoint when talking to the local
                // GeoServer's RESTconfig API
                var url = options.url.replace(this.urlPortRegEx, "$1/");
                if (this.localGeoServerBaseUrl) {
                    if (url.indexOf(this.localGeoServerBaseUrl) == 0) {
                        // replace local GeoServer url with /geoserver/
                        options.url = url.replace(
                            new RegExp("^" + this.localGeoServerBaseUrl),
                            "/geoserver/"
                        );
                        return;
                    }
                    var localUrl = this.localGeoServerBaseUrl.replace(
                        this.urlPortRegEx, "$1/");
                    if(url.indexOf(localUrl + "rest/") === 0) {
                        options.url = url.replace(new RegExp("^" +
                            localUrl), "/geoserver/");
                        return;
                    }
                }
                // use the proxy for all non-local requests
                if(this.proxy && options.url.indexOf(this.proxy) !== 0 &&
                        options.url.indexOf(window.location.protocol) === 0) {
                    var parts = options.url.replace(/&$/, "").split("?");
                    var params = Ext.apply(parts[1] && Ext.urlDecode(
                        parts[1]) || {}, options.params);
                    url = Ext.urlAppend(parts[0], Ext.urlEncode(params));
                    delete options.params;
                    options.url = this.proxy + encodeURIComponent(url);
                }
            },
            "requestexception": function(conn, response, options) {
                if(options.failure) {
                    // exceptions are handled elsewhere
                } else {
                    this.mapPlugins[0].busyMask && this.mapPlugins[0].busyMask.hide();
                    var url = options.url;
                    if (response.status == 401 && url.indexOf("http" != 0) &&
                                            url.indexOf(this.proxy) === -1) {
                        var submit = function() {
                            form.getForm().submit({
                                waitMsg: "Logging in...",
                                success: function(form, action) {
                                    win.close();
                                    document.cookie = action.response.getResponseHeader("Set-Cookie");
                                    // resend the original request
                                    Ext.Ajax.request(options);
                                },
                                failure: function(form, action) {
                                    var username = form.items.get(0);
                                    var password = form.items.get(1);
                                    username.markInvalid();
                                    password.markInvalid();
                                    username.focus(true);
                                },
                                scope: this
                            });
                        }.bind(this);
                        var win = new Ext.Window({
                            title: "GeoNode Login",
                            modal: true,
                            width: 230,
                            autoHeight: true,
                            layout: "fit",
                            items: [{
                                xtype: "form",
                                autoHeight: true,
                                labelWidth: 55,
                                border: false,
                                bodyStyle: "padding: 10px;",
                                url: "/accounts/ajax_login",
                                waitMsgTarget: true,
                                errorReader: {
                                    // teach ExtJS a bit of RESTfulness
                                    read: function(response) {
                                        return {
                                            success: response.status == 200,
                                            records: []
                                        };
                                    }
                                },
                                defaults: {
                                    anchor: "100%"
                                },
                                items: [{
                                    xtype: "textfield",
                                    name: "username",
                                    fieldLabel: "Username"
                                }, {
                                    xtype: "textfield",
                                    name: "password",
                                    fieldLabel: "Password",
                                    inputType: "password"
                                }, {
                                    xtype: "hidden",
                                    name: "csrfmiddlewaretoken",
                                    value: this.csrfToken
                                }, {
                                    xtype: "button",
                                    text: "Login",
                                    inputType: "submit",
                                    handler: submit
                                }]
                            }],
                            keys: {
                                "key": Ext.EventObject.ENTER,
                                "fn": submit
                            }
                        });
                        win.show();
                        var form = win.items.get(0);
                        form.items.get(0).focus(false, 100);
                    } else if (response.status != 405 && url != "/geoserver/rest/styles") {
                        // 405 from /rest/styles is ok because we use it to
                        // test whether we're authenticated or not
                        this.displayXHRTrouble(response);
                    }
                }
            },
            scope: this
        });
        
        // register the color manager with every color field, for Styler
        Ext.util.Observable.observeClass(gxp.form.ColorField);
        gxp.form.ColorField.on({
            render: function(field) {
                var manager = new Styler.ColorManager();
                manager.register(field);
            }
        });

        // global beforeunload handler
        window.onbeforeunload = (function() {
            if (this.fireEvent("beforeunload") === false) {
                return "If you leave this page, unsaved changes will be lost.";
            }
        }).bind(this);
        
        // limit combo boxes to the window they belong to - fixes issues with
        // list shadow covering list items
        Ext.form.ComboBox.prototype.getListParent = function() {
            return this.el.up(".x-window") || document.body;
        };
        
        // don't draw window shadows - allows us to use autoHeight: true
        // without using syncShadow on the window
        Ext.Window.prototype.shadow = false;
        
        if (!config.map) {
            config.map = {};
        }
        config.map.numZoomLevels = config.map.numZoomLevels || 22;

        GeoExplorer.superclass.constructor.apply(this, arguments);

        this.mapID = this.initialConfig.id;
    },
    
    displayXHRTrouble: function(response) {
        response.status && Ext.Msg.show({
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
                }
            }
        });
    },
    
    loadConfig: function(config) {
        config.tools = (config.tools || []).concat({
            ptype: "gxp_zoom",
            actionTarget: {target: "paneltbar", index: 4}
        }, {
            ptype: "gxp_navigationhistory",
            actionTarget: {target: "paneltbar", index: 6}
        }, {
            ptype: "gxp_zoomtoextent",
            actionTarget: {target: "paneltbar", index: 8}
        }, {
            ptype: "gxp_layertree",
            outputConfig: {id: "treecontent"},
            outputTarget: "layertree"
        }, {
            ptype: "gxp_zoomtolayerextent",
            actionTarget: "treecontent.contextMenu"
        }, {
            ptype: "gxp_addlayers",
            actionTarget: "treetbar",
            createExpander: function() {
                return new GeoExplorer.CapabilitiesRowExpander({
                    ows: this.localGeoServerBaseUrl + "ows"
                });
            }
        }, {
            ptype: "gxp_removelayer",
            actionTarget: ["treetbar", "treecontent.contextMenu"]
        }, {
            ptype: "gxp_layerproperties",
            layerPanelConfig: {
                "gxp_wmslayerpanel": {rasterStyling: true}
            },
            actionTarget: ["treetbar", "treecontent.contextMenu"]
        }, {
            ptype: "gxp_styler",
            rasterStyling: true,
            actionTarget: ["treetbar", "treecontent.contextMenu"]
        }, {
            ptype: "gxp_legend",
            outputTarget: 'legend',
            outputConfig: {
                autoScroll: true,
                title: null
            }
        }, {
            ptype: "gxp_print",
            includeLegend: true,
            printCapabilities: window.printCapabilities,
            actionTarget: {target: "paneltbar", index: 3}
        });
        GeoExplorer.superclass.loadConfig.apply(this, arguments);
    },
    
    initMapPanel: function() {
        this.mapItems = [{
            xtype: "gxp_scaleoverlay"
        }, {
            xtype: "gx_zoomslider",
            vertical: true,
            height: 100,
            plugins: new GeoExt.ZoomSliderTip({
                template: "<div>"+this.zoomSliderTipText+": {zoom}<div>"
            })
        }];
        this.mapPlugins = [{
            ptype: "gxp_loadingindicator", 
            onlyShowOnFirstLoad: true
        }];
         
        GeoExplorer.superclass.initMapPanel.apply(this, arguments);
    },
    
    /**
     * Method: initPortal
     * Create the various parts that compose the layout.
     */
    initPortal: function() {
        this.on("beforeunload", function() {
            if (this.modified) {
                this.showMetadataForm();
                return false;
            }
        }, this);

        this.on("ready", function() {
            this.mapPanel.layers.on({
                "update": function() {this.modified |= 1;},
                "add": function() {this.modified |= 1;},
                "remove": function(store, rec) {
                    this.modified |= 1;
                },
                scope: this
            });
        });

       var layersContainer = new Ext.Panel({
            id: "layertree",
            autoScroll: true,
            border: false,
            title: this.layersContainerText,
            tbar: {
                id: 'treetbar'
            }
        });

        var layerTree;
        this.on("ready", function(){
            var startSourceId = null;
            for (var id in this.layerSources) {
                source = this.layerSources[id];
                if (source.store && source instanceof gxp.plugins.WMSSource &&
                                source.url.indexOf("/geoserver/wms" === 0)) {
                    startSourceId = id;
                }
            }
            // find the add layers plugin
            var addLayers = null;
            for (var key in this.tools) {
                var tool = this.tools[key];
                if (tool.ptype === "gxp_addlayers") {
                    addLayers = tool;
                    addLayers.startSourceId = startSourceId;
                }
            }
            if (!this.fromLayer && !this.mapID) {
                if (addLayers !== null) {
                    addLayers.showCapabilitiesGrid();
                }
            }

            // add custom tree contextmenu items
            layerTree = Ext.getCmp("treecontent");
        }, this);

        var layersTabPanel = new Ext.TabPanel({
            border: false,
            deferredRender: false,
            items: [
                layersContainer, {
                xtype: 'panel',
                title: this.legendPanelText,
                layout: 'fit', 
                id: 'legend', 
                split: true
            }],
            activeTab: 0
        });

        //needed for Safari
        var westPanel = new Ext.Panel({
            layout: "fit",
            collapseMode: "mini",
            header: false,
            split: true,
            items: [layersTabPanel],
            region: "west",
            width: 250
        });

        this.toolbar = new Ext.Toolbar({
            disabled: true,
            id: 'paneltbar',
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
        
        var showContextMenu;
        this.googleEarthPanel = new gxp.GoogleEarthPanel({
            mapPanel: this.mapPanel,
            listeners: {
                "beforeadd": function(record) {
                    return record.get("group") !== "background";
                },
                "show": function() {
                    // disable layers toolbar, selection and context menu
                    layerTree.contextMenu.on("beforeshow", OpenLayers.Function.False);
                    this.on(
                        "beforelayerselectionchange", OpenLayers.Function.False
                    );
                    Ext.getCmp("treetbar").disable();
                },
                "hide": function() {
                    var layerTree = Ext.getCmp("treecontent");
                    if (layerTree) {
                        // enable layers toolbar, selection and context menu
                        layerTree.contextMenu.un("beforeshow", OpenLayers.Function.False);
                        this.un(
                            "beforelayerselectionchange", OpenLayers.Function.False
                        );
                        Ext.getCmp("treetbar").enable();
                    }
                },
                scope: this
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
            contentEl: 'header-wrapper'
        });

        Lang.registerLinks();

        this.portalItems = [
            header, {
                region: "center",
                xtype: "container",
                layout: "fit",
                border: false,
                hideBorders: true,
                items: {
                    layout: "border",
                    deferredRender: false,
                    tbar: this.toolbar,
                    items: [
                        this.mapPanelContainer,
                        westPanel
                    ],
                    ref: "../../main"
                }
            }
        ];
        
        GeoExplorer.superclass.initPortal.apply(this, arguments);
    },
    
    createTools: function() {
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
                handler: this.showMetadataForm,
                scope: this,
                iconCls: "icon-save"
            }),
            new Ext.Action({
                tooltip: this.publishActionText,
                handler: this.makeExportDialog,
                scope: this,
                iconCls: 'icon-export',
                disabled: !this.mapID
            }),
            "-",
            enable3DButton
        ];
        this.on("saved", function() {
            // enable the "Publish Map" button
            tools[1].enable();
            this.modified ^= this.modified & 1;
        }, this);

        return tools;
    },

    /** private: method[makeExportDialog]
     *
     * Create a dialog providing the HTML snippet to use for embedding the 
     * (persisted) map, etc. 
     */
    makeExportDialog: function() { 
        new Ext.Window({
            title: this.publishActionText,
            layout: "fit",
            width: 380,
            autoHeight: true,
            items: [{
                xtype: "gxp_embedmapdialog",
                url: this.rest + this.mapID + "/embed" 
            }]
        }).show();
    },

    /** private: method[initMetadataForm]
     *
     * Initialize metadata entry form.
     */
    initMetadataForm: function(){
        
        var titleField = new Ext.form.TextField({
            width: '95%',
            fieldLabel: this.metaDataMapTitle,
            value: this.about.title,
            allowBlank: false,
            enableKeyEvents: true,
            listeners: {
                "valid": function() {
                    saveAsButton.enable();
                    saveButton.enable();
                },
                "invalid": function() {
                    saveAsButton.disable();
                    saveButton.disable();
                }
            }
        });

        var abstractField = new Ext.form.TextArea({
            width: '95%',
            height: 200,
            fieldLabel: this.metaDataMapAbstract,
            value: this.about["abstract"]
        });

        var metaDataPanel = new Ext.FormPanel({
            bodyStyle: {padding: "5px"},          
            labelAlign: "top",
            items: [
                titleField,
                abstractField
            ]
        });

        metaDataPanel.enable();
        
        var saveAsButton = new Ext.Button({
            text: this.metadataFormSaveAsCopyText,
            disabled: !this.about.title,
            handler: function(e){
                this.about.title = titleField.getValue();
                this.about["abstract"] = abstractField.getValue();
                this.metadataForm.hide();
                this.save(true);
            },
            scope: this
        });
        var saveButton = new Ext.Button({
            text: this.metadataFormSaveText,
            disabled: !this.about.title,
            handler: function(e){
                this.about.title = titleField.getValue();
                this.about["abstract"] = abstractField.getValue();
                this.metadataForm.hide();
                this.save();
            },
            scope: this
        });

        this.metadataForm = new Ext.Window({
            title: this.metaDataHeader,
            closeAction: 'hide',
            items: metaDataPanel,
            modal: true,
            width: 400,
            autoHeight: true,
            bbar: [
                "->",
                saveAsButton,
                saveButton,
                new Ext.Button({
                    text: this.metadataFormCancelText,
                    handler: function() {
                        titleField.setValue(this.about.title);
                        abstractField.setValue(this.about["abstract"]);
                        this.metadataForm.hide();
                    },
                    scope: this
                })
            ]
        });
    },

    /** private: method[showMetadataForm]
     *  Shows the window with a metadata form
     */
    showMetadataForm: function() {
        if(!this.metadataForm) {
            this.initMetadataForm();
        }

        this.metadataForm.show();
    },

    updateURL: function() {
        /* PUT to this url to update an existing map */
        return this.rest + this.mapID + '/data';
    },

    /** api: method[save]
     *  :arg as: ''Boolean'' True if map should be "Saved as..."
     *
     *  Subclasses that load config asynchronously can override this to load
     *  any configuration before applyConfig is called.
     */
    save: function(as){
        var config = this.getState();
        
        if (!this.mapID || as) {
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
                    this.fireEvent("saved", id);
                }, 
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
                    this.fireEvent("saved", this.mapID);
                }, 
                scope: this
            });         
        }
    }
});
