/**
 * Copyright (c) 2009 The Open Planning Project
 */

// http://www.sencha.com/forum/showthread.php?141254-Ext.Slider-not-working-properly-in-IE9
// TODO re-evaluate once we move to Ext 4
Ext.override(Ext.dd.DragTracker, {
    onMouseMove: function (e, target) {
        if (this.active && Ext.isIE && !Ext.isIE9 && !e.browserEvent.button) {
            e.preventDefault();
            this.onMouseUp(e);
            return;
        }
        e.preventDefault();
        var xy = e.getXY(), s = this.startXY;
        this.lastXY = xy;
        if (!this.active) {
            if (Math.abs(s[0] - xy[0]) > this.tolerance || Math.abs(s[1] - xy[1]) > this.tolerance) {
                this.triggerStart(e);
            } else {
                return;
            }
        }
        this.fireEvent('mousemove', this, e);
        this.onDrag(e);
        this.fireEvent('drag', this, e);
    }
});

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
     * ``String`` username of current authenticated GeoNode user
     */
    username: "",

    /**
     * api: config[localGeoServerBaseUrl]
     * ``String`` url of the local GeoServer instance
     */
    localGeoServerBaseUrl: "",

    /**
     * api: config[localCSWBaseUrl]
     * ``String`` url of the local CS-W instance
     */
    localCSWBaseUrl: "",

    /**
     * api: config[hypermapRegistryUrl]
     * ``String`` url of the HHypermap Registry instance
     */
    hypermapRegistryUrl: "",

    /**
     * api: config[mapProxyUrl]
     * ``String`` url of the MapProxy instance
     */
    mapProxyUrl: "",

    /**
     * api: config[solrUrl]
     * ``String`` url of the Solr instance
     */
    solrUrl: "",

    /**
     * api: config[useMapOverlay]
     * ``Boolean`` Should we add a scale overlay to the map? Set to false
     * to not add a scale overlay.
     */
    useMapOverlay: null,

    siteUrl: "",

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


    searchFields : [],

    gxSearchBar : null,

    loginWin: null,

    registerWin: null,

    worldMapSourceKey: null,

    hglSourceKey: null,

    //public variables for string literals needed for localization
    addLayersButtonText: "UT:Add Layers",
    arcGisRestLabel: 'UT: Add ArcGIS REST Server',
    areaActionText: "UT:Area",
    backgroundContainerText: "UT:Background",
    connErrorTitleText: "UT:Connection Error",
    connErrorText: "UT:The server returned an error",
    connErrorDetailsText: "UT:Details...",
    feedAdditionLabel: "UT:Add feeds",
    flickrText: "UT:Flickr",
    googleEarthBtnText: "UT:Google Earth",
    heightLabel: 'UT: Height',
    helpLabel: 'UT: Help',
    infoButtonText: "UT:Info",
    largeSizeLabel: 'UT:Large',
    layerAdditionLabel: "UT: Add another server",
    layerLocalLabel: 'UT:Upload your own data',
    layerContainerText: "UT:Map Layers",
    layerPropertiesText: 'UT: Layer Properties',
    layerPropertiesTipText: 'UT: Change layer format and style',
    layerStylesText: 'UT:Edit Styles',
    layerStylesTipText: 'UT:Edit layer styles',
    layerSelectionLabel: "UT:View available data from:",
    layersContainerText: "UT:Data",
    layersPanelText: "UT:Layers",
    legendPanelText: "UT:Legend",
    lengthActionText: "UT:Length",
    loadingMapMessage: "UT:Loading Map...",
    mapSizeLabel: 'UT: Map Size',
    maxMapLayers: 75,
    maxLayersTitle: 'UT:Warning',
    maxLayersText: 'UT:You now have %n layers in your map.  With more than %max layers you may experience problems with layer ordering, info balloon display, and general performance. ',
    measureSplitText: "UT:Measure",
    metadataFormCancelText : "UT:Cancel",
    metadataFormSaveAsCopyText : "UT:Save as Copy",
    metadataFormSaveText : "UT:Save",
    metadataFormCopyText : "UT:Copy",
    metaDataHeader: 'UT:About this Map View',
    metaDataMapAbstract: 'UT:Abstract (brief description)',
    metaDataMapIntroText: 'UT:Introduction (tell visitors more about your map view)',
    metaDataMapTitle: 'UT:Title',
    metaDataMapUrl: 'UT:UserUrl',
    miniSizeLabel: 'UT: Mini',
    addCategoryActionText: 'UT:Add Category',
    addCategoryActionTipText: 'UT: Add a new category to the layer tree',
    renameCategoryActionText: 'UT: Rename Category',
    renameCategoryActionTipText: 'UT: Rename this category',
    removeCategoryActionText: 'UT: Remove Category',
    removeCategoryActionTipText: 'UT: Remove this category and layers',
    navActionTipText: "UT:Pan Map",
    navNextAction: "UT:Zoom to Next Extent",
    navPreviousActionText: "UT:Zoom to Previous Extent",
    premiumSizeLabel: 'UT: Premium',
    printTipText: "UT:Print Map",
    printBtnText: "UT:Print",
    printWindowTitleText: "UT:Print Preview",
    propertiesText: "UT:Properties",
    publishActionText: 'UT:Link To Map',
    publishBtnText: 'UT:Link',
    removeLayerActionText: "UT:Remove Layer",
    removeLayerActionTipText: "UT:Remove Layer",
    revisionBtnText: "UT:Revisions",
    saveFailMessage: "UT: Sorry, your map could not be saved.",
    saveFailTitle: "UT: Error While Saving",
    saveMapText: "UT: Save Map",
    saveMapBtnText: "UT:Save",
    saveMapAsText: "UT: Copy",
    saveNotAuthorizedMessage: "UT: You Must be logged in to save this map.",
    shareLayerText: 'UT: Share Layer',
    smallSizeLabel: 'UT: Small',
    sourceLoadFailureMessage: 'UT: Error contacting server.\n Please check the url and try again.',
    switchTo3DActionText: "UT:Switch to Google Earth 3D Viewer",
    streetViewBtnText: "UT:Street View",
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
    zoomVisibleButtonText: "UT:Zoom to Original Map Extent",
    picasaText: 'Picasa',
    youTubeText: 'YouTube',
    hglText: "Harvard Geospatial Library",
    uploadLayerText: 'Upload Layer',
    createLayerText: 'Create Layer',
    rectifyLayerText: 'Rectify Layer',
    submitendpointText: 'Submit a Map Service',
    worldmapDataText: 'Search',
    externalDataText: 'External Data',
    leavePageWarningText: 'If you leave this page, unsaved changes will be lost.',

    constructor: function(config) {
        this.config = config;
        this.popupCache = {};
        this.propDlgCache = {};
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
            "beforeunload",

            "setLayerTree"
        );

        // add old ptypes
        Ext.preg("gx_wmssource", gxp.plugins.WMSSource);
        Ext.preg("gx_olsource", gxp.plugins.OLSource);
        Ext.preg("gx_googlesource", gxp.plugins.GoogleSource);
        Ext.preg("gx_gnsource", gxp.plugins.GeoNodeSource);

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
                    if (url.indexOf(localUrl + "rest/") === 0) {
                        options.url = url.replace(new RegExp("^" +
                            localUrl), "/geoserver/");
                        return;
                    }
                }
                // use the proxy for all non-local requests
                if(this.proxy && options.url.indexOf(this.proxy) !== 0 &&
                    options.url.indexOf("http") === 0) {
                    var parts = options.url.replace(/&$/, "").split("?");
                    var params = Ext.apply(parts[1] && Ext.urlDecode(
                        parts[1]) || {}, options.params);
                    url = Ext.urlAppend(parts[0], Ext.urlEncode(params));
                    if (!params['keepPostParams'])
                        delete options.params;
                    options.url = this.proxy + encodeURIComponent(url);
                }
            },
            "requestexception": function(conn, response, options) {
                if (options.failure) {
                    // exceptions are handled elsewhere
                } else {
                    this.mapPlugins[0].busyMask && this.mapPlugins[0].busyMask.hide();
                    var url = options.url;
                    if (response.status == 401 && url.indexOf("http" != 0) &&
                        url.indexOf(this.proxy) === -1) {
                        this.showLoginWindow(options);
                    } else {
                        //this.displayXHRTrouble(response);
                    }
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

        // global beforeunload handler
        window.onbeforeunload = (function() {
            if (this.fireEvent("beforeunload") === false) {
                return this.leavePageWarningText;
            }
        }).createDelegate(this);

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
        config.map.numZoomLevels = 22;

        OpenLayers.Map.prototype.Z_INDEX_BASE = {
            BaseLayer: 100,
            Overlay: 325,
            Feature: 3000,
            Popup: 3025,
            Control: 4000
        };



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
                if (result == "ok") {
                    var details = new Ext.Window({
                        id: 'displayXHRTrouble',
                        title: response.status + " " + response.statusText,
                        width: 400,
                        height: 300,
                        items: {
                            xtype: "container",
                            cls: "error-details",
                            html: response.responseText
                        },
                        autoScroll: true,
                        buttons: [
                            {
                                text: "OK",
                                handler: function() {
                                    details.close();
                                }
                            }
                        ]
                    });
                    details.show();
                }
            }
        });
    },

    loadConfig: function(config) {
        var beforeLoad = function(proxy, params) {
            params.headers = {
                'X-CSRFToken': Ext.util.Cookies.get('csrftoken')
            };
        };
        var found = false;
        for (var key in config.sources) {
            var source = config.sources[key];
            if (source.ptype === "gxp_cataloguesource" && source.url === config.localCSWBaseUrl) {
                found = true;
                Ext.apply(source.proxyOptions, {
                    listeners: {
                        "beforeload": beforeLoad
                    }
                });
                break;
            }
        }
        if (found === false) {
            config.sources['csw'] = {
                ptype: "gxp_cataloguesource",
                url: config.localCSWBaseUrl,
                proxyOptions: {
                    listeners: {
                        "beforeload": beforeLoad
                    }
                }
            };
        }
        config.tools = (config.tools || []).concat(
            {
                ptype: "gxp_layermanager",
                groups: (config.map.groups || config.treeconfig),
                id: "treecontentmgr",
                outputConfig: {
                    id: "treecontent",
                    autoScroll: true,
                    tbar: {id: 'treetbar'}
                },
                outputTarget: "westpanel"
            },{
                ptype: "gxp_zoomtolayerextent",
                actionTarget: "treecontent.contextMenu"
            },{
                ptype: "gxp_addcategory",
                actionTarget: ["treecontent.contextMenu"]
            },{
                ptype: "gxp_renamecategory",
                actionTarget: ["treecontent.contextMenu"]
            },{
                ptype: "gxp_removecategory",
                actionTarget: ["treecontent.contextMenu"]
            },{
                ptype: "gxp_removelayer",
                actionTarget: ["treecontent.contextMenu"]
            }, {
                id: "layerproperties_id",
                ptype: "gxp_layerproperties",
                layerPanelConfig: {
                    "gxp_wmslayerpanel": {rasterStyling: true}
                },
                actionTarget: ["treecontent.contextMenu"]
            },{
                ptype: "gxp_layershare",
                actionTarget: ["treecontent.contextMenu"]
            },{
                ptype: "gxp_styler",
                rasterStyling: true,
                actionTarget: ["treecontent.contextMenu"]
            });
        GeoExplorer.superclass.loadConfig.apply(this, arguments);

        var oldLayerChange = gxp.plugins.FeatureEditor.prototype.onLayerChange;
        var localUrl = this.config.localGeoServerBaseUrl;

        gxp.plugins.FeatureManager.prototype.redrawMatchingLayers = function (record) {
            var name = record.get("name");
            var source = record.get("source");
            var updated = false;
            this.target.mapPanel.layers.each(function (candidate) {
                if (candidate.get("source") === source && candidate.get("name") === name) {
                    var layer = candidate.getLayer();
                    layer.redraw(true);
                    if (!updated) {
                        Ext.Ajax.request({
                            url:"/data/" + layer.params.LAYERS + "/ajax_layer_update/",
                            method:"POST",
                            params:{layername:layer.params.LAYERS},
                            success:function (result, request) {
                                if (result.responseText != "True") {
                                } else {
                                }
                            },
                            failure:function (result, request) {
                            }
                        });
                    }
                    updated = true;
                }
            });
        }

        var oldInitComponent = gxp.plugins.FeatureEditorGrid.prototype.initComponent;
        gxp.plugins.FeatureEditorGrid.prototype.initComponent = function(){
            oldInitComponent.apply(this);
            if (this.customEditors["Description"] != undefined && this.customEditors["Description"].field.maxLength == undefined) {
                this.customEditors["Description"].addListener("startedit",
                    function(el, value) {
                        var htmlEditWindow = new Ext.Window({
                                id: 'displayXHRTrouble',
                                title: 'HTML Editor',
                                renderTo: Ext.getBody(),
                                width: 600,
                                height: 300,
                                frame: true,
                                layout: 'fit',
                                closeAction: 'destroy',
                                items: [{
                                    xtype: "panel",
                                    layout: "fit",
                                    style: {height:190},
                                    items: [{
                                        xtype: "textarea",
                                        id: "html_textarea",
                                        value: this.getValue(),
                                        style: {height:190}
                                    }]
                                }],
                                bbar: [
                                    "->",
                                    //saveAsButton,
                                    new Ext.Button({
                                        id: 'saveAsButtonBbar',
                                        text: "Save",
                                        cls:'x-btn-text',
                                        handler: function() {
                                            this.editing = true;
                                            this.setValue(nicEditors.findEditor('html_textarea').getContent());
                                            this.completeEdit();
                                            htmlEditWindow.destroy();
                                        },
                                        scope: this
                                    }),
                                    new Ext.Button({
                                        id: 'cancelButtonBbar',
                                        text: 'Cancel',
                                        cls:'x-btn-text',
                                        handler: function() {
                                            htmlEditWindow.destroy();
                                        },
                                        scope: this
                                    })
                                ]
                            }
                        );

                        htmlEditWindow.show();
                        var myNicEditor = new nicEditor({fullPanel : true,  maxHeight: 190, iconsPath: nicEditIconsPath}).panelInstance('html_textarea')
                        return true;
                    }
                );
            }
        }

    },

    //Check permissions for selected layer and enable/disable feature edit buttons accordingly
    checkLayerPermissions:function (layerRecord) {

        var buttons = this.tools["gn_layer_editor"].actions;

        var toggleButtons = function(enabled) {
            for (var i=0; i < buttons.length; i++) {
                enabled ? buttons[i].enable() : buttons[i].disable();
            }
        }

        //Disable if layer is null or selected layer in tree doesn't match input layer
        var tree_node =  Ext.getCmp("treecontent").getSelectionModel().getSelectedNode();
        if (layerRecord == null) {
            toggleButtons(false);
        }
        else {
            //Proceed if this is a local queryable WMS layer
            var layer = layerRecord.getLayer();
            if (this.layerSources[layerRecord.get("source")] instanceof gxp.plugins.GeoNodeSource) {
                Ext.Ajax.request({
                    url:"/data/" + layer.params.LAYERS + "/ajax-edit-check",
                    method:"POST",
                    success:function (result, request) {
                        if (result.status != 200) {
                            toggleButtons(false);
                        } else {
                            layer.displayOutsideMaxExtent = true;
                            layer.redraw();
                            toggleButtons(true);
                        }
                    },
                    failure:function (result, request) {
                        toggleButtons(false);
                    }
                });
            } else {
                toggleButtons(false);
            }
        }
    },

    showLoginWindow: function(options) {

        this.loginWin = null;
        var submit = function() {
            form = this.loginWin.items.get(0);
            form.getForm().submit({
                waitMsg: "Logging in...",
                success: function(form, action) {
                    this.loginWin.close();
                    this.propDlgCache = {};
                    document.cookie = action.response.getResponseHeader("Set-Cookie");
                    if (options) {
                        // resend the original request
                        Ext.Ajax.request(options);
                    }
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


        this.loginWin = new Ext.Window({
            id: 'loginWin',
            title: "WorldMap Login",
            modal: true,
            width: 230,
            autoHeight: true,
            layout: "fit",
            items: [
                {
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
                    items: [
                        {
                            xtype: "textfield",
                            name: "username",
                            fieldLabel: "Username"
                        },
                        {
                            xtype: "textfield",
                            name: "password",
                            fieldLabel: "Password",
                            inputType: "password"
                        },
                        {
                            xtype: "hidden",
                            name: "csrfmiddlewaretoken",
                            value: this.csrfToken
                        },
                        {
                            xtype: "button",
                            text: "Login",
                            inputType: "submit",
                            handler: submit
                        }
                    ]
                }
            ],
            keys: {
                "key": Ext.EventObject.ENTER,
                "fn": submit
            }
        });

        var form = this.loginWin.items.get(0);
        form.items.get(0).focus(false, 100);
        this.loginWin.show();
    },

    addInfo : function() {
        var queryableLayers = this.mapPanel.layers.queryBy(function(x) {
            return x.get("queryable");
        });
        var geoEx = this;


        queryableLayers.each(function(x) {
            var dl = x.getLayer();
            if (dl.name != "HighlightWMS" && !dl.attributes) {
                var category = x.get("group") != "" && x.get("group") != undefined && x.get("group") ? x.get("group") : "General";
                x.set("group", category);
            }
        }, this);

    },

    /**
     * Remove a feed layer from the SelectFeatureControl (if present) when that layer is removed from the map.
     * If this is not done, the layer will remain on the map even after the record is deleted.
     * @param record
     */
    removeFromSelectControl:  function(record){
        if (this.selectControl ) {
            var recordLayer = record.getLayer();
            //SelectControl might have layers array or single layer object
            if (this.selectControl.layers != null){
                for (var x = 0; x < this.selectControl.layers.length; x++)
                {
                    var selectLayer = this.selectControl.layers[x];
                    var selectLayers = this.selectControl.layers;
                    if (selectLayer.id === recordLayer.id) {
                        selectLayers.splice(x,1);
                        this.selectControl.setLayer(selectLayers);
                    }
                }
            }
            if (this.selectControl.layer != null) {
                if (recordLayer.id === this.selectControl.layer.id) {
                    this.selectControl.setLayer([]);
                }
            }
        }
    },

    initMapPanel: function() {
        this.mapItems = [
            {
                xtype: "gx_zoomslider",
                vertical: true,
                height: 100,
                plugins: new GeoExt.ZoomSliderTip({
                    template: "<div>" + this.zoomSliderTipText + ": {zoom}<div>"
                })
            }
        ];

        OpenLayers.IMAGE_RELOAD_ATTEMPTS = 5;
        OpenLayers.Util.onImageLoadErrorColor = "transparent";

        GeoExplorer.superclass.initMapPanel.apply(this, arguments);

        var incrementLayerStats = function(layer) {
            Ext.Ajax.request({
                url: "/data/layerstats/",
                method: "POST",
                params: {layername:layer.params.LAYERS}
            });
        }
        this.mapPlugins = [{
            ptype: "gxp_loadingindicator",
            onlyShowOnFirstLoad: true
        }];

        this.mapPanel.map.events.register("preaddlayer", this, function(e) {
            var layer = e.layer;
            if (layer instanceof OpenLayers.Layer.WMS) {
                layer.events.on({
                    "loadend": function() {
                        incrementLayerStats(layer);
                        layer.events.unregister("loadend", this, arguments.callee);
                    },
                    scope: this
                });
            }
        });

    },

    /**
     * Method: initPortal
     * Create the various parts that compose the layout.
     */
    initPortal: function() {
        this.on("beforeunload", function() {
            if (this.modified && this.config["edit_map"]) {
                this.showMetadataForm();
                return false;
            }
        }, this);

        var geoEx = this;
        // TODO: make a proper component out of this
        var mapOverlay = this.createMapOverlay();
        this.mapPanel.add(mapOverlay);

        if (!this.busyMask) {
            this.busyMask = new Ext.LoadMask(
                Ext.getBody(), {
                    msg: this.loadingMapMessage
                }
            );
        }
        this.busyMask.show();

        var addLayerButton = new Ext.Button({
            id: "worldmap_addlayers_button",
            disabled: false,
            text: '<span class="x-btn-text">' + this.addLayersButtonText + '</span>',
            handler : this.showSearchWindow,
            scope: this
        });

        this.on("ready", function() {

            this.addInfo();
            this.mapPanel.layers.on({
                "update": function() {
                    this.modified |= 1;
                },
                "add": function() {
                    this.modified |= 1;
                },
                "remove": function(store, rec) {
                    this.modified |= 1;
                },
                scope: this
            });

            if (this.busyMask) {
                this.busyMask.hide();
            }

            //Show the info window if it's the first time here
            if (this.config.first_visit)
                this.showInfoWindow();

            //If there are feeds on the map, there will be a SelectFeature control.
            //Activate it now.
            if (this.selectControl)
                this.selectControl.activate();

            var startSourceId = null;
            for (var id in this.layerSources) {
                source = this.layerSources[id];
                if (source instanceof gxp.plugins.GeoNodeSource)  {
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
                    addLayers.catalogSourceKey = startSourceId;
                } else if (tool.ptype == "gxp_layermanager") {
                    this.layerTree = tool;
                    this.fireEvent("setLayerTree");
                }
            }
            if (addLayers !== null) {
                addLayers.layerTree = this.layerTree;
                if (!this.fromLayer && !this.mapID) {
                    addLayers.showCapabilitiesGrid();
                }
            }
        }, this);



        this.gxSearchBar = new gxp.SearchBar({
            target: this
        });
        var searchPanel = new Ext.Panel({
            id: 'search_panel_id',
            anchor: "100% 5%",
            items: [this.gxSearchBar]
        });


        //needed for Safari
        var westPanel = new Ext.Panel({
            layout: "fit",
            id: "westpanel",
            border: false,
            collapseMode: "mini",
            header: false,
            split: true,
            bbar: [searchPanel],
            region: "west",
            width: 280
        });


        var gridWinPanel = new Ext.Panel({
            id: 'gridWinPanel',
            collapseMode: "mini",
            title: 'Identify Results',
            region: "west",
            autoScroll: true,
            split: true,
            items: [],
            width:200
        });

        var gridResultsPanel = new Ext.Panel({
            id: 'gridResultsPanel',
            title: 'Feature Details',
            region: "center",
            collapseMode: "mini",
            autoScroll: true,
            split: true,
            items: [],
            width: 400
        });


        var identifyWindow = new Ext.Window({
            id: 'queryPanel',
            layout: "border",
            closeAction: "hide",
            items: [gridWinPanel, gridResultsPanel],
            width: 600,
            height: 400
        });




        this.toolbar = new Ext.Toolbar({
            disabled: true,
            id: 'paneltbar',
            items: [
                addLayerButton,
                this.createTools()
            ]
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
                    var layerTree = Ext.getCmp("treecontent");
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
            id: "mapPnlCntr",
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
            id: 'header-temp',
            region: "north",
            autoHeight: true,
            contentEl: 'header-wrapper'
        });

        Lang.registerLinks();

        this.portalItems = [
            header, {
                id: "portalItems",
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


    reloadWorldMapSource : function(layerRecords) {
        var geoEx = this;
        if (this.worldMapSourceKey == null)
            this.setWorldMapSourceKey();

        geoEx.addWorldMapLayers(layerRecords);

    },

    setWorldMapSourceKey : function() {
        for (var id in this.layerSources) {
            source = this.layerSources[id];
            var isIninstanceofGeoNodeSource = (source instanceof gxp.plugins.GeoNodeSource);
            // if (isIninstanceofGeoNodeSource && source.url.replace(this.urlPortRegEx, "$1/").indexOf(
            //     this.localGeoServerBaseUrl.replace(this.urlPortRegEx, "$1/")) === 0) {
            //     this.worldMapSourceKey = id;
            //}
            if (isIninstanceofGeoNodeSource){
                this.worldMapSourceKey = id;
            }
        }
    },

    setHGLSourceKey : function() {
        for (var id in this.layerSources) {
            source = this.layerSources[id];
            if (source instanceof gxp.plugins.HGLSource) {
                this.hglSourceKey = id;
            }
        }
        if (this.hglSourceKey == null)
        {
            var hglSource = this.addLayerSource({"config":{"url":"http://hgl.harvard.edu/cgi-bin/tilecache/tilecache.cgi?", "ptype":"gxp_hglsource"}});
            this.hglSourceKey = hglSource.id;
        }

    },

    addWorldMapLayers: function(records) {
        if (this.worldMapSourceKey == null) {
            this.setWorldMapSourceKey();
        }
        var wmSource = this.layerSources[this.worldMapSourceKey];
        if (wmSource) {
            for (var i = 0; i < records.length; i++) {
                var record = records[i];
                // add an existing layers
                if ('uuid' in record.data){
                    if (record.data['service_type'] == 'Hypermap:WorldMap'){
                        this.addLayerAjax(wmSource, this.worldMapSourceKey, record);
                    } else {
                        url = this.hypermapRegistryUrl + '/registry/hypermap/layer/' + record.data['uuid'] + '/map/wmts/' + record.data['name'] + '/default_grid/${z}/${x}/${y}.png';
                        var hhSource = this.addLayerSource({"config":{"url":url, "ptype":"gxp_gnsource"}});
                        this.addLayerAjax(hhSource, hhSource.id, record);
                    }
                } else {
                    // newly uploaded and created layers
                    this.addLayerAjax(wmSource, this.worldMapSourceKey, record);
                }
            }
        }
    },

    /** private: method[getMapProjection]
     *  :returns: ``OpenLayers.Projection``
     */
    getMapProjection: function() {
        var projConfig = this.mapPanel.map.projection;
        return this.target.mapPanel.map.getProjectionObject() ||
            (projConfig && new OpenLayers.Projection(projConfig)) ||
            new OpenLayers.Projection("EPSG:4326");
    },

    /**
    Add a layer to the Map.
    Creates an instance for any existing WM layer or any Registry layer for being added to the map.
    */
    addLocalLayer: function(thisRecord, source, layerStore, key){
        //Get all the required WMS parameters from the GeoNode/Worldmap database
        // instead of GetCapabilities

        var typename = this.searchTable.getlayerTypename(thisRecord);
        var tiled = thisRecord.get("tiled") || true;

        var layer_bbox = [
            parseFloat(thisRecord.get('min_x')),
            parseFloat(thisRecord.get('min_y')),
            parseFloat(thisRecord.get('max_x')),
            parseFloat(thisRecord.get('max_y'))
            ];

        var layer_detail_url = this.mapProxyUrl + '/registry/hypermap/layer/' + thisRecord.get('uuid') + '/';

        var layer = {
            "styles": "",
            "group": "General",
            "name": thisRecord.get('name'),
            "title": thisRecord.get('title'),
            "url": layer_detail_url + 'map/wmts/' + typename.replace('geonode:', '') + '/default_grid/${z}/${x}/${y}.png',
            "abstract": thisRecord.get('abstract'),
            "visibility": true,
            "queryable": true,
            "disabled": false,
            "srs": thisRecord.get('srs'),
            "bbox": layer_bbox,
            "transparent": true,
            "llbbox": layer_bbox,
            "source": key,
            "buffer": 0,
            "tiled": true,
            "local": thisRecord.get('service_type') === 'Hypermap:WorldMap'
        };

        if (thisRecord.get('service_type') === 'Hypermap:WorldMap'){
            layer_detail_url = 'http://worldmap.harvard.edu/data/' + thisRecord.get('name');
        };

        if(layer.local){
            // url is always the generic GeoServer endpoint for WM layers
            // layer.url = this.localGeoServerBaseUrl + 'wms';
            layer.url = this.localGeoServerBaseUrl.replace("/geoserver/", "/geoserver/wms");
        };

        if(thisRecord.get('ServiceType') === 'ESRI:ArcGIS:ImageServer' || thisRecord.get('ServiceType') === 'ESRI:ArcGIS:MapServer'){
            layer.url = thisRecord.get('url');
            layer.name = thisRecord.get('title');
            if (layer.srs == null){
              //Assume that the bbox needs to be transformed to web mercator
              //delete layer.bbox;
              layer_bbox = [thisRecord.get('min_x'),thisRecord.get('min_y'),thisRecord.get('max_x'),thisRecord.get('max_y')];
              layer.bbox = new OpenLayers.Bounds(layer_bbox).transform("EPSG:4326", this.map.projection).toArray();
            }
            this.addEsriSourceAndLayer(layerStore, layer, layer_detail_url);
        }else{
            this.loadRecord(source, layerStore, layer, layer_detail_url);
        }
    },

    /**
    * Check if the user has the permission for displaying the WM layer before adding it to the map.
    */
    testLayerPermission: function(thisRecord, source, layerStore, key, is_new_layer){
        var self = this;
        // not sure when the layer name is LayerName
        if('LayerName' in thisRecord.data){
            var name = thisRecord.get('LayerName');
        } else {
            var name = thisRecord.get('name');
        }
        $.ajax({
            url: '/data/' + name,
            method: 'GET',
            complete: function(xhr, status){
                if (xhr.status == 200){
                    if(is_new_layer){
                      self.addNewWMLayer(thisRecord, source, layerStore, key);
                    } else {
                      self.addLocalLayer(thisRecord, source, layerStore, key)
                    }
                }
            },
            dataType: 'jsonp'
        });
    },

    /**
    * Creates an instance for a new WM layer (created or uploaded) for being added to the map.
    */
    addNewWMLayer: function(thisRecord, source, layerStore, key){
      if (this.worldMapSourceKey == null)
          this.setWorldMapSourceKey();
      var source = this.layerSources[this.worldMapSourceKey];
      var name = thisRecord.get('name');
      var tiled = thisRecord.get('tiled');
      var layer_detail_url = 'http://worldmap.harvard.edu/data/' + name;
      var layer = null;

      $.ajax({
          url: "/maps/addgeonodelayer/?layername=" + name,
          type: "GET",
          dataType: 'json',
          async: false,
          //params: {layername:name},
          success: function(data){
            layer = data['layer']
            layer.source = key;
            layer.buffer = 0;
            layer.tiled = true;
            layer.local = true;
          },
          error: function(jqXHR, textStatus, errorThrown){
            alert('Exeption:' + exception);
          }
      });

      this.loadRecord(source, layerStore, layer, layer_detail_url);

    },

    addLayerAjax: function (dataSource, dataKey, dataRecord) {
        var geoEx = this;
        var key = dataKey;
        var source = dataSource;

        var layerStore = this.mapPanel.layers;
        /*
        var isLocal = source instanceof gxp.plugins.GeoNodeSource &&
          source.url.replace(this.urlPortRegEx, "$1/").indexOf(
                this.localGeoServerBaseUrl.replace(
                    this.urlPortRegEx, "$1/")) === 0;
        */
        // I believe this check is not needed any more (it was used by the previous add remote layers tool)
        var isLocal = true;
        //for (var i = 0, ii = records.length; i < ii; ++i) {
        var thisRecord = dataRecord;
        if (isLocal){
            var authorized = true;
            // layer from solr
            if ('uuid' in thisRecord.data){
                if (!$.parseJSON(thisRecord.get('is_public'))){
                   geoEx.testLayerPermission(thisRecord, source, layerStore, key, false);
                } else {
                    // hack here
                    geoEx.addLocalLayer(thisRecord, source, layerStore, key);
                }
            } else {
                // newly uploaded and created layers
                geoEx.testLayerPermission(thisRecord, source, layerStore, key, true);
            }
        } else {
            //Not a local GeoNode layer, use source's standard method for creating the layer.
            var layer = thisRecord.get("name");
            var record = source.createLayerRecord({
                name: layer,
                source: key,
                buffer: 0
            });
            //alert(layer + " created after FAIL");
            if (record) {
                if (record.get("group") === "background") {
                    var pos = layerStore.queryBy(
                        function(rec) {
                            return rec.get("group") === "background"
                        }).getCount();
                    layerStore.insert(pos, [record]);
                } else {
                    category = "General";
                    record.set("group", category);

                    geoEx.layerTree.addCategoryFolder({"group":record.get("group")}, true);
                    layerStore.add([record]);
                }
            }
        }
        //}
        this.searchWindow.hide();
    },

    addEsriSourceAndLayer: function(layerStore, layer, layer_detail_url){
      this.addLayerSource({
          config: {url: layer.url, ptype: 'gxp_arcrestsource'},
          callback: function(source_id){
              layer.source = source_id;
              source = this.layerSources[source_id];
              this.loadRecord(source, this.mapPanel.layers, layer, layer_detail_url);
          }
        });
    },

    /**
    Load a layer in the map.
    */
    loadRecord: function(source, layerStore, config, layer_detail_url){
        var record = source.createLayerRecord(config);
        var geoEx = this;
        record.selected = true;
        // record.data.detail_url = thisRecord.get('LayerUrl').indexOf('worldmap.harvard.edu') > -1 ?
        //         '/data/' + thisRecord.get('LayerName') :
        //         this.mapproxy_backend + JSON.parse(thisRecord.get('Location')).layerInfoPage;
        record.data.detail_url = layer_detail_url;

        if (record) {
            if (record.get("group") === "background") {
                var pos = layerStore.queryBy(
                    function(rec) {
                        return rec.get("group") === "background"
                    }).getCount();
                layerStore.insert(pos, [record]);

            } else {
                category = record.get("group");
                if (!category || category == '')
                    record.set("group", "General");

                geoEx.layerTree.addCategoryFolder({"group":record.get("group")}, true);
                layerStore.add([record]);

                //geoEx.reorderNodes(record.getLayer());
                geoEx.layerTree.overlayRoot.findDescendant("layer", record.getLayer()).select();
            }
        };
    },

    initSearchPanel: function() {

        if (this.worldMapSourceKey == null)
            this.setWorldMapSourceKey();
        var selectedSource = this.layerSources[this.worldMapSourceKey];

        var sources = {};
        for (var key in this.layerSources) {
            var source = this.layerSources[key];
            if (source instanceof gxp.plugins.CatalogueSource) {
                var obj = {};
                obj[key] = source;
                Ext.apply(sources, obj);
                if (source.url == this.config.localCSWBaseUrl) {
                    selectedSource = source;
                }
            }
        }


//        this.catalogPanel = new gxp.CatalogueSearchPanel({
//            autoScroll: false,
//            title: 'WorldMap Data',
//            header: false,
//            layout: 'fit',
//            border: true,
//                sources: sources,
//                selectedSource: selectedSource,
//                topicCategories: this.config.topicCategories,
//                map: this.mapPanel.map,
//                listeners: {
//                    'addlayer': function(cmp, sourceKey, layerConfig) {
//                        var source = this.layerSources[sourceKey];
//                        var bounds = OpenLayers.Bounds.fromArray(layerConfig.bbox);
//                        var mapProjection = this.mapPanel.map.getProjection();
//                        var bbox = bounds.transform(layerConfig.srs, mapProjection);
//                        layerConfig.srs = mapProjection;
//                        layerConfig.bbox = bbox.toArray();
//                        var record = source.createLayerRecord(layerConfig);
//                        record.set("group", layerConfig.subject);
//                        var layerTree = Ext.getCmp("treecontent")
//                        if (layerTree) {
//                            layerTree.addCategoryFolder({"group":layerConfig.subject});
//                        }
//
//                        this.mapPanel.layers.add(record);
//                    },
//                    scope: this
//                }
//            });
    },

    /** private: method[createMapOverlay]
     * Builds the :class:`Ext.Panel` containing components to be overlaid on the
     * map, setting up the special configuration for its layout and
     * map-friendliness.
     */
    createMapOverlay: function() {
        var cgaLink = new Ext.BoxComponent({
            html:'<div class="cga-link" onclick="javascript:window.open(\'http://gis.harvard.edu\', \'_blank\');"><a href="http://gis.harvard.edu">Center for Geographic Analysis</a></div>'
        });

        var scaleLinePanel = new Ext.BoxComponent({
            autoEl: {
                tag: "div",
                cls: "olControlScaleLine overlay-element overlay-scaleline"
            }
        });

        scaleLinePanel.on('render', function() {
            var scaleLine = new OpenLayers.Control.ScaleLine({
                div: scaleLinePanel.getEl().dom,
                geodesic: true
            });

            this.mapPanel.map.addControl(scaleLine);
            scaleLine.activate();
        }, this);

        var zoomSelectorWrapper = new Ext.Panel({
            id: 'zoom_selector_Wrapper',
            cls: 'overlay-element overlay-scalechooser',
            ctCls: 'transparent-panel',
            border: false,
            width: 130
        });

        this.on("ready", function() {
            var zoomStore = new GeoExt.data.ScaleStore({
                map: this.mapPanel.map
            });

            var zoomSelector = new Ext.form.ComboBox({
                id: 'zoomselectorinfo',
                emptyText: this.zoomSelectorText,
                tpl: '<tpl for="."><div class="x-combo-list-item">1 : {[parseInt(values.scale)]}</div></tpl>',
                editable: false,
                triggerAction: 'all',
                mode: 'local',
                store: zoomStore,
                width: 120
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
            }

            setScale.call(this);
            this.mapPanel.map.events.register('zoomend', this, setScale);

            zoomSelectorWrapper.add(zoomSelector);
            zoomSelectorWrapper.doLayout();
        }, this);

        var mapOverlay = new Ext.Panel({
            id: 'map_overlay',
            // title: "Overlay",
            cls: 'map-overlay',
            items: [
                scaleLinePanel,
                zoomSelectorWrapper,
                cgaLink
            ]
        });

        mapOverlay.on("afterlayout", function() {
            scaleLinePanel.getEl().dom.style.position = 'relative';
            scaleLinePanel.getEl().dom.style.display = 'inline';

            mapOverlay.getEl().on("click", function(x) {
                x.stopEvent();
            });
            mapOverlay.getEl().on("mousedown", function(x) {
                x.stopEvent();
            });
        }, this);

        return mapOverlay;
    },



    createTools: function() {
        var toolGroup = "toolGroup";
        var mapPanel = this.mapPanel;
        var busyMask = null;
        var geoEx = this;

        var info = {controls: []};
        // create an info control to show introductory text window
        var infoButton = new Ext.Button({
            id: 'infoButtonId',
            tooltip: 'About',
            text: '<span class="x-btn-text">About</span>',
            handler: this.showInfoWindow,
            scope:this
        });


        var flickrMenuItem = {
            text: this.flickrText,
            iconCls: "icon-flickr",
            scope:this,
            disabled: false,
            hidden: false,
            handler: function() {
                this.showFeedDialog('gx_flickrsource')
            },
            scope: this
        };

        var picasaMenuItem = {
            text: this.picasaText,
            iconCls: "icon-picasa",
            scope:this,
            disabled: false,
            hidden: false,
            handler: function() {
                this.showFeedDialog('gx_picasasource')
            },
            scope: this
        };


        var youtubeMenuItem = {
            text: this.youTubeText,
            iconCls: "icon-youtube",
            scope:this,
            disabled: false,
            hidden: false,
            handler: function() {
                this.showFeedDialog('gx_youtubesource')
            },
            scope: this
        };

        var hglMenuItem = {
            text: this.hglText,
            iconCls: "icon-harvard",
            scope:this,
            handler: function() {
                this.showFeedDialog('gx_hglfeedsource')
            },
            scope: this
        };

        var languageSelect = {
            xtype: 'box',
            contentEl: 'langselect',
            cls: "language-overlay-element"
        };

        //this.mapPanel.add(languageSelect);


        var publishAction = new Ext.Action({
            id: 'worldmap_publish_tool',
            tooltip: this.publishActionText,
            handler: this.makeExportDialog,
            scope: this,
            text: '<span class="x-btn-text">' + this.publishBtnText + '</span>',
            disabled: !this.mapID
        });

        var saveText = (this.config["edit_map"] || this.about["urlsuffix"] !== "boston") ? this.saveMapBtnText : this.saveMapAsText;
        var tools = [
            new Ext.Button({
                id: 'saveTextId',
                tooltip: saveText,
                handler: this.showMetadataForm,
                scope: this,
                disabled: !this.config["edit_map"] && this.about["urlsuffix"] !== "boston",
                text: '<span class="x-btn-text">' + saveText + '</span>'
            }),
            publishAction,
            infoButton,
            "->"
        ];

        //Only show this for Boston map; silly hack
        if (this.about["urlsuffix"] == 'boston') {
            tools.splice(13,0,new GeoExplorer.SocialExplorer(this));
        }


        this.on("saved", function() {
            // enable the "Publish Map" button
            publishAction.enable();
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

        var mapConfig = this.getState();
        var treeConfig = [];
        for (x = 0,max = this.layerTree.overlayRoot.childNodes.length; x < max; x++) {
            node = this.layerTree.overlayRoot.childNodes[x];
            treeConfig.push({group : node.text, expanded:  node.expanded.toString()  });
        }


        mapConfig.map['groups'] = treeConfig;


        Ext.Ajax.request({
            url: "/maps/snapshot/create",
            method: 'POST',
            jsonData: mapConfig,
            success: function(response, options) {
                var encodedSnapshotId = response.responseText;
                if (encodedSnapshotId != null) {
                    new Ext.Window({
                        id: 'encodedSnapshotId',
                        title: this.publishActionText,
                        layout: "fit",
                        width: 380,
                        autoHeight: true,
                        items: [
                            {
                                xtype: "gx_linkembedmapdialog",
                                linkUrl: this.rest + (this.about["urlsuffix"] ? this.about["urlsuffix"] : this.mapID) + '/' + encodedSnapshotId,
                                linkMessage: '<span style="font-size:10pt;">Paste link in email or IM:</span>',
                                publishMessage: '<span style="font-size:10pt;">Paste HTML to embed in website:</span>',
                                url: this.rest + (this.about["urlsuffix"] ? this.about["urlsuffix"] : this.mapID) + '/' + encodedSnapshotId + "/embed"
                            }
                        ]
                    }).show();
                }
            },
            failure: function(response, options) {
                Ext.Msg.alert('Error', response.responseText, this.showMetadataForm);
                return false;
            },
            scope: this
        });
    },



    /** private: method[initMetadataForm]
     *
     * Initialize metadata entry form.
     */
    initMetadataForm: function() {

        var geoEx = this;
        var saveButton = Ext.getCmp("gx_saveButton");
        var saveAsButton = Ext.getCmp("gx_saveAsButton");
        var titleField = new Ext.form.TextField({
            id: 'titleField',
            width: '95%',
            fieldLabel: this.metaDataMapTitle,
            value: this.config["edit_map"] ? this.about.title : "",
            allowBlank: false,
            enableKeyEvents: true,
            listeners: {
                "valid": function() {
                    if (urlField.isValid()) {
                        if (this.config["edit_map"])
                            saveButton.enable();
                        if (!saveAsButton.hidden)
                            saveAsButton.enable();
                    }
                },
                "invalid": function() {
                    //saveAsButton.disable();
                    saveButton.disable();
                    if (!saveAsButton.hidden)
                        saveAsButton.disable();
                },
                scope: this
            }
        });

        //Make sure URL is not taken; if it is, show list of taken url's that start with field value
        Ext.apply(Ext.form.VTypes, {
            UniqueMapId : this.mapID,
            UniqueUrl: function(value, field) {

                var allowedChars = value.match(/^(\w+[-]*)+$/g);
                if (!allowedChars) {
                    this.UniqueUrlText = "URL's can only contain letters, numbers, dashes & underscores."
                    return false;
                }

                Ext.Ajax.request({
                    url: "/maps/checkurl/",
                    method: 'POST',
                    params : {query:value, mapid: this.UniqueMapId},
                    success: function(response, options) {
                        var urlcount = Ext.decode(response.responseText).count;
                        if (urlcount > 0) {
                            this.UniqueUrlText = "The following URL's are already taken:";
                            var urls = Ext.decode(response.responseText).urls;
                            var isValid = true;
                            for (var u in urls) {
                                if (urls[u].url != undefined && urls[u].url != null)
                                    this.UniqueUrlText += "<br/>" + urls[u].url;
                                if (urls[u].url == value) {
                                    isValid = false;
                                }

                            }
                            if (!isValid)
                                field.markInvalid(this.UniqueUrlText);
                        }
                    },
                    failure: function(response, options) {
                        Ext.Msg.alert('Error', response.responseText, this.showMetadataForm);
                        return false;

                    },
                    scope: this
                });
                return true;
            },

            UniqueUrlText: "The following URL's are already taken, please choose another"
        });

        var urlField = new Ext.form.TextField({
            id: 'url_field',
            width:'30%',
            fieldLabel: this.metaDataMapUrl + "<br/><span style='font-style:italic;'>http://" + document.location.hostname + "/maps/</span>",
            labelSeparator:'',
            enableKeyEvents: true,
            validationEvent: 'onblur',
            vtype: 'UniqueUrl',
            itemCls:'x-form-field-inline',
            ctCls:'x-form-field-inline',
            value: this.config["edit_map"] ? this.about["urlsuffix"] : "",
            listeners: {
                "valid": function() {
                    if (titleField.isValid()) {
                        if (this.config["edit_map"])
                            saveButton.enable();
                        if (!saveAsButton.hidden)
                            saveAsButton.enable();
                    }
                },
                "invalid": function() {
                    //saveAsButton.disable();
                    saveButton.disable();
                    if (!saveAsButton.hidden)
                        saveAsButton.disable();
                },
                scope: this
            }
        });

        var checkUrlBeforeSave = function(as) {
            Ext.getCmp('gx_saveButton').disable();
            Ext.getCmp('gx_saveAsButton').disable();

            Ext.Ajax.request({
                url: "/maps/checkurl/",
                method: 'POST',
                params : {query:urlField.getValue(), mapid: as ? 0 : geoEx.mapID},
                success: function(response, options) {
                    var urlcount = Ext.decode(response.responseText).count;
                    var rt = "";
                    var isValid = true;
                    if (urlcount > 0) {
                        rt = "The following URL's are already taken:";
                        var urls = Ext.decode(response.responseText).urls;

                        for (var u in urls) {
                            if (urls[u].url != undefined && urls[u].url != null)
                                rt += "<br/>" + urls[u].url;
                            if (urls[u].url == urlField.getValue()) {
                                isValid = false;
                            }

                        }
                        if (!isValid) {
                            urlField.markInvalid(rt);
                            Ext.getCmp('gx_saveButton').enable();
                            Ext.getCmp('gx_saveAsButton').enable();
                            return false;
                        }

                    }
                    if (isValid) {
                        geoEx.about.title = Ext.util.Format.stripTags(titleField.getValue());
                        geoEx.about["abstract"] = Ext.util.Format.stripTags(abstractField.getValue());
                        geoEx.about["urlsuffix"] = urlField.getValue();
                        geoEx.about["introtext"] = nicEditors.findEditor('intro_text_area').getContent();
                        geoEx.save(as);
                        geoEx.initInfoTextWindow();
                    }
                },
                failure: function(response, options) {
                    Ext.getCmp('gx_saveButton').enable();
                    Ext.getCmp('gx_saveAsButton').enable();
                    return false;
                    //Ext.Msg.alert('Error', response.responseText, geoEx.showMetadataForm);
                },
                scope: this
            });
        };

        var abstractField = new Ext.form.TextArea({
            id: 'abstract_field',
            width: '95%',
            height: 50,
            fieldLabel: this.metaDataMapAbstract,
            value: this.about["abstract"]
        });


        var introTextField = new Ext.form.TextArea({
            width: 550,
            height: 200,
            fieldLabel: this.metaDataMapIntroText,
            id: "intro_text_area",
            value: this.about["introtext"]
        });


        var metaDataPanel = new Ext.FormPanel({
            id: 'meta_data_panel',
            bodyStyle: {padding: "5px"},
            labelAlign: "top",
            items: [
                titleField,
                urlField,
                abstractField,
                introTextField
            ]
        });

        metaDataPanel.enable();

        var saveButton = new Ext.Button({
            id: 'gx_saveButton',
            text: this.metadataFormSaveText,
            cls:'x-btn-text',
            disabled: !this.about.title || !this.config["edit_map"],
            handler: function(e) {
                checkUrlBeforeSave(false);
            },
            scope: this
        });

        var saveAsButton = new Ext.Button({
            id: 'gx_saveAsButton',
            text: this.metadataFormSaveAsCopyText,
            cls:'x-btn-text',
            disabled: !this.about.title,
            hidden: this.about["urlsuffix"] !== "boston",
            handler: function(e) {
                checkUrlBeforeSave(true);
            },
            scope: this
        });

        this.metadataForm = new Ext.Window({
            id: 'metadataForm',
            title: this.metaDataHeader,
            closeAction: 'hide',
            items: metaDataPanel,
            modal: true,
            width: 600,
            autoHeight: true,
            bbar: [
                "->",
                //saveAsButton,
                saveButton,
                saveAsButton,
                new Ext.Button({
                    id: 'metadataFormCancelText',
                    text: this.metadataFormCancelText,
                    cls:'x-btn-text',
                    handler: function() {
                        titleField.setValue(this.about.title);
                        abstractField.setValue(this.about["abstract"]);
                        urlField.setValue(this.about["urlsuffix"]);
                        introTextField.setValue(this.about["introtext"]);
                        this.metadataForm.hide();
                    },
                    scope: this
                })
            ]
        });

    },

    initInfoTextWindow: function() {
        this.infoTextPanel = new Ext.FormPanel({
            id: 'info_text_panel',
            bodyStyle: {padding: "5px"},
            labelAlign: "top",
            preventBodyReset: true,
            autoScroll:false,
            html: this.about['introtext']
        });

        this.infoTextPanel.enable();


        this.infoTextWindow = new Ext.Window({
            id: 'infoTextWindow',
            title: this.about.title,
            closeAction: 'hide',
            items: this.infoTextPanel,
            modal: true,
            width: 500,
            height:400,
            autoScroll: true
        });
    },


    initHelpTextWindow: function() {
        this.helpTextPanel = new Ext.FormPanel({
            id: 'help_text_panel',
            bodyStyle: {padding: "5px"},
            labelAlign: "top",
            preventBodyReset: true,
            autoScroll:false,
            autoHeight:true,
            autoLoad:{url:'/maphelp',scripts:true}
        });

        this.helpTextPanel.enable();

        this.helpTextWindow = new Ext.Window({
            id: 'helpTextWindow',
            title: this.helpLabel,
            closeAction: 'hide',
            items: this.helpTextPanel,
            modal: true,
            width: 1000,
            height:500,
            autoScroll: true
        });
    },

    initUploadPanel: function() {
        this.uploadPanel = new Ext.Panel({
            id: 'worldmap_update_panel',
            title: this.uploadLayerText,
            header: false,
            contentEl: 'uploadDiv',
            autoScroll: true
        });
    },

    initCreatePanel: function() {
        this.createPanel = new Ext.Panel({
            id: 'worldmap_create_panel',
            title: this.createLayerText,
            header: false,
            contentEl: 'createDiv',
            autoScroll: true
        });
    },

    initWarperPanel: function() {
        this.warperPanel = new Ext.Panel({
            id: 'worldmap_warper_panel',
            title: this.rectifyLayerText,
            header: false,
            contentEl: 'warpDiv',
            autoScroll: true
        });
    },

    initSubmitEndpointPanel: function() {
        this.submitEndpointPanel = new Ext.Panel({
            id: 'worldmap_submitendpoint_panel',
            title: this.submitendpointText,
            header: false,
            contentEl: 'submitEndpointDiv',
            autoScroll: true
        });
    },



    initTabPanel: function() {
//        var feedSourceTab = new gxp.FeedSourceDialog({
//            target: this,
//            title: "Feeds",
//            renderTo: "feedDiv"
//        });

        this.dataTabPanel = new Ext.TabPanel({
            activeTab: 0,
            region:'center',
            items: [{
                contentEl: 'searchDiv',
                title: this.worldmapDataText,
                autoScroll: true
            }]
        });

        if (this.config["edit_map"] && Ext.get("uploadDiv")) {
            this.dataTabPanel.add(this.uploadPanel);
            if (this.config["db_datastore"]) {
                this.dataTabPanel.add(this.createPanel);
            }
        }

        this.dataTabPanel.add(this.warperPanel);
        this.dataTabPanel.add(this.submitEndpointPanel);
    },


    /*  Set up a simplified map config with just background layers and
     the current map extent, to be used on the data search map */
    getBoundingBoxConfig: function() {
        // start with what was originally given
        var state = this.getState();
        state.tools = [];
        // update anything that can change
        var center = this.mapPanel.map.getCenter();
        Ext.apply(state.map, {
            center: [0, 0],
            zoom: 0,
            layers: []
        });

        // include all layer config (and add new sources)
        this.mapPanel.layers.each(function(record) {
            if (record.get("group") === "background") {
                var layer = record.getLayer();
                if (layer.displayInLayerSwitcher && layer.getVisibility() === true) {
                    var id = record.get("source");
                    var source = this.layerSources[id];
                    if (!source) {
                        throw new Error("Could not find source for layer '" + record.get("name") + "'");
                    }
                    // add layer
                    state.map.layers.push(source.getConfigForRecord(record));
                    if (!state.sources[id]) {
                        state.sources[id] = Ext.apply({}, source.initialConfig);
                    }
                }
            }
        }, this);

        return state;
    },

    initSearchWindow: function() {
        var mapBounds = this.mapPanel.map.getExtent();
        var llbounds = mapBounds.transform(
            new OpenLayers.Projection(this.mapPanel.map.projection),
            new OpenLayers.Projection("EPSG:4326"));


        this.bbox = new GeoNode.BoundingBoxWidget({
            proxy: "/proxy/?url=",
            viewerConfig:this.getBoundingBoxConfig(),
            renderTo: 'refine',
            height: 350,
            isEnabled: false,
            useGxpViewer: true
        });

        // Pass the bbox widget to heatmap so that it can accesd the search map
        var heatmap = new GeoNode.HeatmapModel({bbox_widget: this.bbox});

        //Pass the heatmap to the searchTable so that it can trigger searches
        this.searchTable = new GeoNode.SearchTable({
            renderTo: 'search_form',
            trackSelection: true,
            permalinkURL: '/data/search',
            // 0. use this one in production
            searchURL: this.solrUrl,
            layerDetailURL: '/data/search/detail',
            constraints: [this.bbox],
            searchParams: {'limit':10, 'bbox': llbounds.toBBOX()},
            searchOnLoad: false,
            heatmap: heatmap
        });

        this.searchTable.hookupSearchButtons('refine');

        var dataCart = new GeoNode.DataCart({
            store: this.searchTable.dataCart,
            renderTo: 'data_cart',
            addToMapButtonFunction: this.addWorldMapLayers,
            addToMapButtonTarget: this
        });

        if (!this.uploadPanel && this.config["edit_map"] && Ext.get("uploadDiv")) {
            this.initUploadPanel();
        }

        if (!this.createPanel && this.config["edit_map"] && this.config["db_datastore"] === true) {
            this.initCreatePanel();
        }

        if (!this.warperPanel) {
            this.initWarperPanel();
        }

        if (!this.submitEndpointPanel) {
            this.initSubmitEndpointPanel();
        }

        if (!this.dataTabPanel) {
            this.initTabPanel();
        }


        this.searchWindow = new Ext.Window({
            id: 'ge_searchWindow',
            title: "Search BETA",
            closeAction: 'hide',
            layout: 'fit',
            width: 900,
            height: 590,
            items: [this.dataTabPanel],
            modal: true,
            autoScroll: true,
            resizable: true,
            bodyStyle: 'background-color:#FFF'
        });
    },

    showFeedDialog:function (selectedOption) {
        if (!this.feedDialog) {
            this.feedDialog = new gxp.FeedSourceDialog({
                title:"Add a GeoRSS Feed",
                closeAction:"hide",
                target:this,
                listeners:{
                    "feed-added":function (ptype, config) {

                        var sourceConfig = {"config":{"ptype":ptype}};
                        if (config.url) {
                            sourceConfig.config["url"] = config.url;
                        }
                        var source = this.addLayerSource(sourceConfig);
                        config.source = source.id;
                        var feedRecord = source.createLayerRecord(config);



                        this.layerTree.addCategoryFolder({"group":feedRecord.get("group")}, true);
                        this.mapPanel.layers.add([feedRecord]);
                        var layer = feedRecord.getLayer();
                        this.layerTree.overlayRoot.findDescendant("layer", layer).select();

                    }, scope:this
                }, scope:this
            });
        }
        this.feedDialog.show();
        this.feedDialog.alignTo(document, 't-t');
        if (selectedOption) {
            this.feedDialog.sourceTypeRadioList.setValue(selectedOption);
        }
    },


    /** private: method[showInfoWindow]
     *  Shows the search window
     */
    showSearchWindow: function() {

        if (!this.searchWindow) {
            this.initSearchWindow();
        }
        this.searchWindow.show();
        this.searchWindow.alignTo(document, 'tl-tl');

        //Apparently the ext slider has a bug in positioning the thumbs.
        // this is a workaround, we do this after the search window has been rendered.
        this.searchTable.dateInput.syncThumb();

        // Don't show the window if >70 layers on map (due to z-index issue with OpenLayers maps)
        if (this.mapPanel.layers.data.items.length > this.maxMapLayers) {
            Ext.Msg.alert(this.maxLayersTitle, this.maxLayersText.replace('%n', this.mapPanel.layers.data.items.length).replace("%max", this.maxMapLayers));
        }
    },




    /** private: method[showInfoWindow]
     *  Shows the window with intro text
     */
    showInfoWindow: function() {
        if (!this.infoTextWindow) {
            this.initInfoTextWindow();
        }
        this.infoTextWindow.show();
        this.infoTextWindow.alignTo(document, 't-t');
    },


    /** private: method[showMetadataForm]
     *  Shows the window with a metadata form
     */
    showMetadataForm: function() {
        if (!this.metadataForm) {
            this.initMetadataForm();
            this.metadataForm.show();
            var metaNicEditor = new nicEditor({fullPanel : true,  maxHeight: 200, iconsPath: nicEditIconsPath}).panelInstance('intro_text_area')

        } else
            this.metadataForm.show();

        this.metadataForm.alignTo(document, 't-t');
        //Ext.getCmp('gx_saveButton').enable();
        //Ext.getCmp('gx_saveAsButton').enable();
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
    save: function(as) {
        var config = this.getState();

        var treeConfig = [];
        for (x = 0,max = this.layerTree.overlayRoot.childNodes.length; x < max; x++) {
            node = this.layerTree.overlayRoot.childNodes[x];
            treeConfig.push({group : node.text, expanded:  node.expanded.toString()  });
        }


        config.map.groups = treeConfig;

        if (!this.mapID || as) {
            /* create a new map */
            Ext.Ajax.request({
                //url: this.rest,
                url: "/maps/new/data",
                method: 'POST',
                jsonData: config,
                success: function(response, options) {
                    var id = JSON.parse(response.responseText)['id']
                    this.mapID = id; //id is url, not mapID
                    this.fireEvent("saved", id);
                    this.metadataForm.hide();
                    Ext.Msg.wait('Saving Map', "Your new map is being saved...");

                    //window.location = response.getResponseHeader("Location");
                    window.location = '/maps/' + id + '/view';
                },
                failure: function(response, options) {
                    if (response.status === 401)
                        this.showLoginWindow(options);
                    else
                        Ext.Msg.alert('Error', response.responseText);

                    Ext.getCmp('gx_saveButton').enable();
                    Ext.getCmp('gx_saveAsButton').enable();
                },
                scope: this
            });
        }
        else {
            /* save an existing map */
            var saveAsButton = Ext.getCmp('gx_saveAsButton');
            Ext.Ajax.request({
                url: this.updateURL(),
                method: 'PUT',
                jsonData: config,
                success: function(response, options) {
                    /* nothing for now */
                    this.fireEvent("saved", this.mapID);
                    this.metadataForm.hide();
                    Ext.getCmp('gx_saveButton').enable();
                    if (!saveAsButton.hidden)
                        saveAsButton.enable();
                    // create thumb
                    createMapThumbnail(this.mapid);
                },
                failure: function(response, options) {
                    if (response.status === 401)
                        this.showLoginWindow(options);
                    else {
                        Ext.Msg.alert('Error', response.responseText);
                        Ext.getCmp('gx_saveButton').enable();
                        if (!saveAsButton.hidden)
                            saveAsButton.enable();
                    }
                },
                scope: this
            });
        }
    },


    addHGL: function(layerTitle, layerName) {
        Ext.Ajax.request({
            url: "/hglServiceStarter/" + layerName,
            method: 'POST',
            success: function(response, options) {
//        layerName = "sde:SDE.CAMCONTOUR";
                if (this.hglSourceKey == null)
                    this.setHGLSourceKey();
                var hglSource = this.layerSources[this.hglSourceKey];
                if (hglSource)
                {
                    var layerConfig = {
                        "title": layerTitle,
                        "name": layerName,
                        "source": this.hglSourceKey,
                        "url": hglSource.url,
                        "group": "Harvard Geospatial Library",
                        "properties": "gxp_wmslayerpanel",
                        "fixed": true,
                        "selected": false,
                        "queryable": true,
                        "disabled": false,
                        "abstract": '',
                        "styles": [],
                        "format": "image/png"
                    }



                    var record = hglSource.createLayerRecord(layerConfig);
                    this.layerTree.addCategoryFolder(record.get("group"), true);

                    this.mapPanel.layers.add([record]);
                    this.layerTree.overlayRoot.findDescendant("layer", record.getLayer()).select();
                }
            },
            failure: function(response, options) {
                Ext.Msg.alert('Restricted', "Access to this layer is restricted");
            },
            scope: this
        });
    }
});
