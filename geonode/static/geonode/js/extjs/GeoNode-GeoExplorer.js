Ext.ns("GeoNode.plugins");

/** api: constructor
 *  .. class:: Save(config)
 *
 *    Plugin for saving maps. Will provide a Save button as an action if not
 *    configured with an empty actions array.
 */
GeoNode.plugins.Save = Ext.extend(gxp.plugins.Tool, {

    // i18n
    metadataFormCancelText : "UT:Cancel",
    metadataFormSaveAsCopyText : "UT:Save as Copy",
    metadataFormSaveText : "UT:Save",
    metaDataHeader: 'UT:About this Map',
    metaDataMapAbstract: 'UT:Abstract',
    metaDataMapTitle: 'UT:Title',
    // end i18n

    /** api: ptype = gn_save */
    ptype: 'gn_save',

    /** private: method[init]
     *  :arg target: ``Object`` The object initializing this plugin.
     */
    init: function(target) {
        GeoNode.plugins.Save.superclass.init.apply(this, arguments);
        this.target.on("beforesave", function(requestConfig, callback) {
            if (this._doSave === true) {
                delete this._doSave;
                if (this.target.id) {
                    requestConfig.url = this.target.rest + this.target.id + "/data";
                } else {
                    requestConfig.url = this.target.rest + "new/data";
                }
                return true;
            } else {
                this.showMetadataForm(callback);
                return false;
            }
        }, this);
        this.target.on("beforehashchange", function(hash) {
            return false;
        });
    },

    /** api: method[addActions]
     *  :returns: ``Array`` The actions added.
     */
    addActions: function() {
        var actions = this.actions || [{
            text: 'Save',
            handler: function() {
                this.target.doAuthorized(["ROLE_ADMINISTRATOR"], function() {
                    this.target.save(this.target.showEmbedWindow);
                }, this);
            },
            scope: this
        }];
        return GeoNode.plugins.Save.superclass.addActions.apply(this, actions);
    },

    /** private: method[initMetadataForm]
     *
     * Initialize metadata entry form.
     */
    initMetadataForm: function(callback){

        var titleField = new Ext.form.TextField({
            width: '95%',
            fieldLabel: this.metaDataMapTitle,
            value: this.target.about.title,
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
            value: this.target.about["abstract"]
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
            disabled: !this.target.about.title,
            handler: function(e){
                delete this.target.id;
                this.target.about.title = Ext.util.Format.stripTags(titleField.getValue());
                this.target.about["abstract"] = Ext.util.Format.stripTags(abstractField.getValue());
                this.metadataForm.hide();
                this._doSave = true;
                this.target.save(this.metadataForm.saveCallback);
            },
            scope: this
        });
        var saveButton = new Ext.Button({
            text: this.metadataFormSaveText,
            disabled: !this.target.about.title,
            handler: function(e){
                this.target.about.title = Ext.util.Format.stripTags(titleField.getValue());
                this.target.about["abstract"] = Ext.util.Format.stripTags(abstractField.getValue());
                this.metadataForm.hide();
                this._doSave = true;
                this.target.save(this.metadataForm.saveCallback);
            },
            scope: this
        });

        this.metadataForm = new Ext.Window({
            title: this.metaDataHeader,
            closeAction: 'hide',
            saveCallback: callback,
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
                        titleField.setValue(this.target.about.title);
                        abstractField.setValue(this.target.about["abstract"]);
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
    showMetadataForm: function(callback) {
        if(!this.metadataForm) {
            this.initMetadataForm(callback);
        } else {
            this.metadataForm.saveCallback = callback;
        }
        this.metadataForm.show();
    }

});

Ext.preg(GeoNode.plugins.Save.prototype.ptype, GeoNode.plugins.Save);

/** api: constructor
 *  .. class:: SaveHyperlink(config)
 *
 *    Plugin for showing hyperlinks for going to the list of maps as well as
 *    going to the current saved map.
 */
GeoNode.plugins.SaveHyperlink = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gn_savehyperlink */
    ptype: 'gn_savehyperlink',

    /** private: method[init]
     *  :arg target: ``Object`` The object initializing this plugin.
     */
    init: function(target) {
        GeoNode.plugins.SaveHyperlink.superclass.init.apply(this, arguments);
        this.titleTemplate = new Ext.Template("<a class='maplist' href='" +
            this.target.rest + "'>Maps</a> / <strong>{title}");
        this.target.on("save", function(id) {
            this.actions[0].update(this.getMapTitle());
        }, this);
    },

    /** api: method[addActions]
     *  :returns: ``Array`` The actions added.
     */
    addActions: function() {
        return GeoNode.plugins.SaveHyperlink.superclass.addActions.apply(this, [
            new Ext.Container({cls: "map-title-header", html: this.getMapTitle()})
        ]);
    },

    /** private: method[getPermalink]
     *  :return: ``String``
     *
     *  Get the permalink for the current map.
     */
    getPermalink: function() {
        permalinkTemplate = new Ext.Template("{protocol}//{host}/maps/{id}");
        return permalinkTemplate.apply({
            protocol: window.location.protocol,
            host: window.location.host,
            id: this.target.id
        });
    },

    /** private: getMapTitle
     *  :return: ``String``
     *
     *  Get the HTML to use in the map title container which is shown in the
     *  top right of the panel top toolbar.
     */
    getMapTitle: function() {
        var title;
        if (this.target.id) {
            title = '<a class="link" href="' + this.getPermalink() + '">' + this.target.about.title + '</a>';
        } else {
            title = "This map is currently unsaved";
        }
        return this.titleTemplate.apply({title: title});
    }

});

Ext.preg(GeoNode.plugins.SaveHyperlink.prototype.ptype, GeoNode.plugins.SaveHyperlink);

GeoNode.plugins.XHRTrouble = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gn_xhrtrouble */
    ptype: 'gn_xhrtrouble',

    // i18n
    connErrorTitleText: "UT:Connection Error",
    connErrorText: "UT:The server returned an error",
    connErrorDetailsText: "UT:Details...",
    // end i18n

    /** private: method[init]
     *  :arg target: ``Object`` The object initializing this plugin.
     */
    init: function(target) {
        // global request proxy and error handling
        OpenLayers.Request.events.on({
            "failure": function(evt) {
                this.displayXHRTrouble(evt.request);
            },
            scope: this
        });
        Ext.util.Observable.observeClass(Ext.data.Connection);
        Ext.data.Connection.on({
            "requestexception": function(conn, response, options) {
                if(!options.failure) {
                    var url = options.url;
                    if (response.status === 401 && url.indexOf("http" !== 0) &&
                                            url.indexOf(this.proxy) === -1) {
                        this.authenticate(options);
                    } else if (response.status != 405 && url != "/geoserver/rest/styles") {
                        // 405 from /rest/styles is ok because we use it to
                        // test whether we're authenticated or not
                        this.displayXHRTrouble(response);
                    }
                }
            },
            scope: this
        });
        GeoNode.plugins.XHRTrouble.superclass.init.apply(this, arguments);
    },

    /** private method[displayXHRTrouble]
     *  :arg respoonse: ``Object`` The XHR response object.
     *
     *  If something goes wrong with an AJAX request, show an error dialog
     *  with a button to view the details (Django error).
     */
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
    }

});

Ext.preg(GeoNode.plugins.XHRTrouble.prototype.ptype, GeoNode.plugins.XHRTrouble);

/** api: constructor
 *  .. class:: LayerInfo(config)
 *
 *    Plugin for navigating to the GeoNode layer info page.
 *    Will only be enabled for local layers.
 */
GeoNode.plugins.LayerInfo = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gxp_removelayer */
    ptype: "gn_layerinfo",

    /** api: config[menuText]
     *  ``String``
     *  i18n text to use on the menu item.
     */
    menuText: "Layer Info",

    /** api: config[iconCls]
     *  ``String``
     *  iconCls to use on the menu item.
     */
    iconCls: "gxp-icon-layerproperties",

    /** api: method[addActions]
     *  :returns: ``Array`` The actions added.
     */
    addActions: function() {
        var actions = GeoNode.plugins.LayerInfo.superclass.addActions.apply(this, [{
            menuText: this.menuText,
            iconCls: this.iconCls,
            disabled: true,
            handler: function() {
                if (this.link) {
                    window.open(this.link);
                }
            },
            scope: this
        }]);
        var layerInfoAction = actions[0];

        this.target.on("layerselectionchange", function(record) {
            var remote=null;
            if (record) {
                if (record.get("source_params")) {
                    remote = record.get("source_params").name;
                }
                else {
                    var store = this.target.sources[record.get("source")];
                    if (store && store["name"]){
                        remote = store["name"];
                    }
                }
                // TODO is there a way to get this from a template variable?
                var layerid = (remote? remote + ":" : "") + this.target.selectedLayer.get("name");
                if (record && record.getLayer() instanceof OpenLayers.Layer.ArcGIS93Rest) {
                    layerid = layerid.replace("show:","");
                }

                this.link =  "/layers/" + layerid;
            }

            layerInfoAction.setDisabled(!record || (!record.get('restUrl') && !remote));


        }, this);
        return actions;
    }
});

Ext.preg(GeoNode.plugins.LayerInfo.prototype.ptype, GeoNode.plugins.LayerInfo);

/** api: constructor
 *  .. class:: LayerManager(config)
 *
 *    Plugin for adding a tree of layers with their legend to a
 *    :class:`gxp.Viewer`. Also provides a context menu on layer nodes.
 */
/** api: example
 *  If you want to change the vendor-specific legend_options parameter that
 *  is sent to the WMS for GetLegendGraphic you can use ``baseAttrs`` on the
 *  ``loader`` config:
 *
 *  .. code-block:: javascript
 *
 *    var layerManager = new GeoNode.plugins.LayerManager({
 *        loader: {
 *            baseAttrs: {
 *                baseParams: {
 *                    legend_options: "fontAntiAliasing:true;fontSize:11;fontName:Arial;fontColor:#FFFFFF"
 *                }
 *            }
 *        }
 *    });
 *
 */
GeoNode.plugins.LayerManager = Ext.extend(gxp.plugins.LayerTree, {

    /** api: ptype = gxp_layermanager */
    ptype: "gxp_layermanager",

    /** api: config[baseNodeText]
     *  ``String``
     *  Text for baselayer node of layer tree (i18n).
     */
    baseNodeText: "Base Maps",

    /** api: config[groups]
     *  ``Object`` The groups to show in the layer tree. Keys are group names,
     *  and values are either group titles or an object with ``title`` and
     *  ``exclusive`` properties. ``exclusive`` means that nodes will have
     *  radio buttons instead of checkboxes, so only one layer of the group can
     *  be active at a time. Optional, the default is
     *
     *  .. code-block:: javascript
     *
     *      groups: {
     *          "default": "Overlays", // title can be overridden with overlayNodeText
     *          "background": {
     *              title: "Base Maps", // can be overridden with baseNodeText
     *              exclusive: true
     *          }
     *      }
     */

    /** private: method[createOutputConfig] */
    createOutputConfig: function() {
        var tree = gxp.plugins.LayerManager.superclass.createOutputConfig.apply(this, arguments);
        Ext.applyIf(tree, Ext.apply({
            cls: "gxp-layermanager-tree",
            lines: false,
            useArrows: true,
            plugins: [{
                ptype: "gx_treenodecomponent"
            }]
        }, this.treeConfig));

        return tree;
    },

    /** private: method[configureLayerNode] */
    configureLayerNode: function(loader, attr) {
        gxp.plugins.LayerManager.superclass.configureLayerNode.apply(this, arguments);
        var legendXType;
        // add a WMS legend to each node created
        if (OpenLayers.Layer.WMS && attr.layer instanceof OpenLayers.Layer.WMS) {
            legendXType = "gx_wmslegend";
        } else if (OpenLayers.Layer.Vector && attr.layer instanceof OpenLayers.Layer.Vector) {
            legendXType = "gx_vectorlegend";
        }
        if (legendXType) {
            var baseParams;
            var access_token = this.target.access_token;
            if (loader && loader.baseAttrs && loader.baseAttrs.baseParams) {
                baseParams = loader.baseAttrs.baseParams;
            } else {
                baseParams = {};
            }
            var layerRecord = this.target.mapPanel.layers.getByLayer(attr.layer);
                layerRecord.store.baseParams = Ext.apply({
                    access_token: access_token
                }, baseParams);
                layerRecord.data.layer.mergeNewParams({access_token: access_token});

            Ext.apply(attr, {
                component: {
                    xtype: legendXType,
                    // TODO these baseParams were only tested with GeoServer,
                    // so maybe they should be configurable - and they are
                    // only relevant for gx_wmslegend.
                    hidden: !attr.layer.getVisibility(),
                    baseParams: Ext.apply(baseParams, {
                        transparent: true,
                        format: "image/png",
                        legend_options: "fontAntiAliasing:true;fontSize:11;fontName:Arial",
                        access_token: access_token
                    }),
                    layerRecord: layerRecord,
                    showTitle: false,
                    // custom class for css positioning
                    // see tree-legend.html
                    cls: "legend"
                }
            });
        }
    }

});

Ext.preg(GeoNode.plugins.LayerManager.prototype.ptype, GeoNode.plugins.LayerManager);

/** api: constructor
 *  .. class:: Print(config)
 *
 *    Provides an action to print the map. Requires GeoExt.ux.PrintPreview,
 *    which is currently mirrored at git://github.com/GeoNode/PrintPreview.git.
 */
GeoNode.plugins.Print = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gxp_print */
    ptype: "gxp_print",

    /** api: config[printService]
     *  ``String``
     *  URL of the print service. Specify either printService
     *  or printCapabilities.
     */
    printService: null,

    /** api: config[printCapabilities]
     *  ``Object``
     *  Capabilities object of the print service. Specify either printService
     *  or printCapabilities.
     */
    printCapabilities: null,

    /** api: config[customParams]
     *  ``Object`` Key-value pairs of custom data to be sent to the print
     *  service. Optional. This is e.g. useful for complex layout definitions
     *  on the server side that require additional parameters.
     */
    customParams: null,

    /** api: config[includeLegend]
     *  ``Boolean`` Should we include the legend in the print? Defaults to false.
     */
    includeLegend: false,

    /** api: config[menuText]
     *  ``String``
     *  Text for print menu item (i18n).
     */
    menuText: "Print Map",

    /** api: config[tooltip]
     *  ``String``
     *  Text for print action tooltip (i18n).
     */
    tooltip: "Print Map",

    /** api: config[text]
     *  ``String``
     *  Text for print action button (i18n).
     */
    buttonText: "Print",

    /** api: config[notAllNotPrintableText]
     *  ``String``
     *  Text for message when not all layers can be printed (i18n).
     */
    notAllNotPrintableText: "Not All Layers Can Be Printed",

    /** api: config[nonePrintableText]
     *  ``String``
     *  Text for message no layers are suitable for printing (i18n).
     */
    nonePrintableText: "None of your current map layers can be printed",

    /** api: config[previewText]
     *  ``String``
     *  Text for print preview text (i18n).
     */
    previewText: "Print Preview",

    /** api: config[openInNewWindow]
     *  ``Boolean``
     *  If true, always open in new window regardless of the browser type.
     */
    openInNewWindow: false,

    /** private: method[constructor]
     */
    constructor: function(config) {
        gxp.plugins.Print.superclass.constructor.apply(this, arguments);
    },

    /** api: method[addActions]
     */
    addActions: function() {
        // don't add any action if there is no print service configured
        if (this.printService !== null || this.printCapabilities != null) {

            var printProvider = new GeoExt.data.PrintProvider({
                capabilities: this.printCapabilities,
                url: this.printService,
                customParams: this.customParams,
                autoLoad: false,
                listeners: {
                    beforedownload: function(provider, url) {
                        if (this.openInNewWindow === true) {
                            window.open(url);
                            return false;
                        }
                    },
                    beforeencodelegend: function(provider, jsonData, legend) {
                        if (legend && legend.ptype === "gxp_layermanager") {
                            var encodedLegends = [];
                            var output = legend.output;
                            var access_token = legend.target.access_token;
                            if (output && output[0]) {
                                output[0].getRootNode().cascade(function(node) {
                                    if (node.component && !node.component.hidden) {
                                        var cmp = node.component;
                                        var encFn = this.encoders.legends[cmp.getXType()];
                                        var legendEncoded = encFn.call(this, cmp, jsonData.pages[0].scale);
                                        try {
                                            if((!legendEncoded[0].classes[0].icons[0].match(/\bformat/gi))) {
                                                legendEncoded[0].classes[0].icons[0] += "&format=image/png";
                                            }
                                        } catch(err) {
                                            console.log(legendEncoded);
                                        }
                                        try {
                                            if((!legendEncoded[0].classes[0].icons[0].match(/\baccess_token/gi))) {
                                                legendEncoded[0].classes[0].icons[0] += "&access_token="+access_token;
                                            } else {
                                                legendEncoded[0].classes[0].icons[0] =
                                                    legendEncoded[0].classes[0].icons[0].replace(/(access_token)(.+?)(?=\&)/, "$1="+access_token);
                                            }
                                        } catch(err) {
                                            console.log(legendEncoded);
                                        }
                                        if (!legendEncoded[0].name) {
                                            legendEncoded[0].name = node.layer.name;
                                        }
                                        encodedLegends = encodedLegends.concat(legendEncoded);
                                    }
                                }, provider);
                            }
                            jsonData.legends = encodedLegends;
                            // cancel normal encoding of legend
                            return false;
                        }
                    },
                    beforeprint: function() {
                        // The print module does not like array params.
                        // TODO Remove when http://trac.geoext.org/ticket/216 is fixed.
                        printWindow.items.get(0).printMapPanel.layers.each(function(l) {
                            var params = l.get("layer").params;
                            for(var p in params) {
                                if (params[p] instanceof Array) {
                                    params[p] = params[p].join(",");
                                }
                            }
                        });
                    },
                    loadcapabilities: function() {
                        if (printButton) {
                            printButton.initialConfig.disabled = false;
                            printButton.enable();
                        }
                    },
                    print: function() {
                        try {
                            printWindow.close();
                        } catch (err) {
                            // TODO: improve destroy
                        }
                    },
                    printException: function(cmp, response) {
                        this.target.displayXHRTrouble && this.target.displayXHRTrouble(response);
                    },
                    scope: this
                }
            });

            var actions = gxp.plugins.Print.superclass.addActions.call(this, [{
                menuText: this.menuText,
                buttonText: this.buttonText,
                tooltip: this.tooltip,
                iconCls: "gxp-icon-print",
                disabled: this.printCapabilities !== null ? false : true,
                handler: function() {
                    var supported = getPrintableLayers();
                    if (supported.length > 0) {
                        var printWindow = createPrintWindow.call(this);
                        showPrintWindow.call(this);
                        return printWindow;
                    } else {
                        // no layers supported
                        Ext.Msg.alert(
                            this.notAllNotPrintableText,
                            this.nonePrintableText
                        );
                    }
                },
                scope: this,
                listeners: {
                    render: function() {
                        // wait to load until render so we can enable on success
                        printProvider.loadCapabilities();
                    }
                }
            }]);

            var printButton = actions[0].items[0];

            var printWindow;

            function destroyPrintComponents() {
                if (printWindow) {
                    // TODO: fix this in GeoExt
                    try {
                        var panel = printWindow.items.first();
                        panel.printMapPanel.printPage.destroy();
                        //panel.printMapPanel.destroy();
                    } catch (err) {
                        // TODO: improve destroy
                    }
                    printWindow = null;
                }
            }

            var mapPanel = this.target.mapPanel;
            function getPrintableLayers() {
                var supported = [];
                mapPanel.layers.each(function(record) {
                    var layer = record.getLayer();
                    if (isPrintable(layer)) {
                        supported.push(layer);
                    }
                });
                return supported;
            }

            function isPrintable(layer) {
                return layer.getVisibility() === true && (
                    layer instanceof OpenLayers.Layer.WMS ||
                    layer instanceof OpenLayers.Layer.OSM ||
                    layer instanceof OpenLayers.Layer.XYZ
                );
            }

            function createPrintWindow() {
                var legend = null;
                if (this.includeLegend === true) {
                    var key, tool;
                    for (key in this.target.tools) {
                        tool = this.target.tools[key];
                        if (tool.ptype === "gxp_legend") {
                            try {
                                legend = (tool.getLegendPanel() ? tool.getLegendPanel() : tool);
                            } catch(err) {
                                legend = tool;
                            }
                            break;
                        }
                    }

                    // if not found, look for a layer manager instead
                    if (!legend || legend === null) {
                        for (key in this.target.tools) {
                            tool = this.target.tools[key];
                            if (tool.ptype === "gxp_layermanager") {
                                legend = tool;
                                break;
                            }
                        }
                    }

                    if (!legend || legend === null) {
                        if (this.target.viewerTools) {
                            for (key in this.target.viewerTools) {
                                tool = this.target.viewerTools[key];
                                if (tool.ptype === "gxp_layermanager") {
                                    legend = tool;
                                    break;
                                }
                                if (tool.ptype === "gxp_legend") {
                                    legend = tool;
                                    break;
                                }
                            }
                        }
                    }
                }
                printWindow = new Ext.Window({
                    title: this.previewText,
                    modal: true,
                    border: false,
                    autoHeight: true,
                    resizable: false,
                    width: 360,
                    items: [
                        new GeoExt.ux.PrintPreview({
                            minWidth: 336,
                            mapTitle: this.target.about && this.target.about["title"],
                            comment: this.target.about && this.target.about["abstract"],
                            printMapPanel: {
                                autoWidth: true,
                                height: Math.min(420, Ext.get(document.body).getHeight()-150),
                                limitScales: true,
                                map: Ext.applyIf({
                                    controls: [
                                        new OpenLayers.Control.Navigation({
                                            zoomWheelEnabled: false,
                                            zoomBoxEnabled: false
                                        }),
                                        new OpenLayers.Control.PanPanel(),
                                        new OpenLayers.Control.ZoomPanel(),
                                        new OpenLayers.Control.Attribution()
                                    ],
                                    eventListeners: {
                                        preaddlayer: function(evt) {
                                            return isPrintable(evt.layer);
                                        }
                                    }
                                }, mapPanel.initialConfig.map),
                                items: [{
                                    xtype: "gx_zoomslider",
                                    vertical: true,
                                    height: 100,
                                    aggressive: true
                                }],
                                listeners: {
                                    afterlayout: function(evt) {
                                        printWindow.setWidth(Math.max(360, this.getWidth() + 24));
                                        printWindow.center();
                                    }
                                }
                            },
                            printProvider: printProvider,
                            includeLegend: this.includeLegend,
                            legend: legend,
                            sourceMap: mapPanel
                        })
                    ],
                    listeners: {
                        beforedestroy: destroyPrintComponents
                    }
                });
                return printWindow;
            }

            function showPrintWindow() {
                printWindow.show();

                // measure the window content width by it's toolbar
                printWindow.setWidth(0);
                var tb = printWindow.items.get(0).items.get(0);
                var w = 0;
                tb.items.each(function(item) {
                    if(item.getEl()) {
                        w += item.getWidth();
                    }
                });
                printWindow.setWidth(
                    Math.max(printWindow.items.get(0).printMapPanel.getWidth(),
                    w + 20)
                );
                printWindow.center();
            }

            return actions;
        }
    }

});

Ext.preg(GeoNode.plugins.Print.prototype.ptype, GeoNode.plugins.Print);

/** api: constructor
 *  .. class:: Composer(config)
 *
 *    The GeoNode Composer application class.
 *    Changes compared to out-of-the-box GeoExplorer:
 *    - before saving a map, show a metadata form
 *    - add a tool that will show the map title and that will have a clickable
 *      link.
 *    - a generic XHRTrouble dialog that gives easier access to underlying
 *      Django errors.
 *    - adds catalogue search through the GeoNode search api
 *    - only enable editing if user has the right permissions
 *    - integrate with GeoNode AJAX login
 *    - publish map will show the iframe text directly, and not a wizard
 *      like interface that GeoExplorer has
 *    - when saving a map, do not set window.location.hash
 *    - use different urls for saving a new map and updating an existing map
 *      than GeoExplorer does.
 */
GeoNode.Composer = window.GeoExplorer && Ext.extend(GeoExplorer.Composer, {

    ajaxLoginUrl: null,

    /** private: method[showUrl]
     *  Do not show the url after map save.
     */
    showUrl: Ext.emptyFn,

    /** api: method[loadConfig]
     *  :arg config: ``Object`` The config object passed to the constructor.
     *
     *  Subclasses that load config asynchronously can override this to load
     *  any configuration before applyConfig is called.
     */
    loadConfig: function(config) {
        // find out what the key of the local source is
        var catalogSourceKey, key;
        for (key in config.sources) {
            var source = config.sources[key];
            if (source.ptype === "gxp_wmscsource" && source.restUrl) {
                catalogSourceKey = key;
                break;
            }
        }
        for (var i=0, ii=config.tools.length; i<ii; i++) {
            if (config.tools[i].ptype === "gxp_styler") {
                config.tools[i].rasterStyling = true;
            }
            if (config.tools[i].ptype === "gxp_addlayers") {
                config.tools[i].search = {
                  selectedSource: 'search'
                };
                config.tools[i].catalogSourceKey = catalogSourceKey;
                config.tools[i].feeds = true;
            }
            if (config.tools[i].ptype === "gxp_print") {
                config.tools[i].includeLegend = true;
            }
        }
        // add catalog source
        config.sources['search'] = {
            ptype: "gxp_geonodeapicataloguesource",
            restUrl: "/gs/rest",
            url: "/api/layers/"
        };

        config.tools.push({
            ptype: 'gn_xhrtrouble'
        }, {
            ptype: 'gn_savehyperlink',
            actionTarget: 'paneltbar'
        }, {
            ptype: 'gn_save',
            actions: []
        }, {
            ptype: "gn_layerinfo",
            actionTarget: ["layers.contextMenu"]
        }, {
            ptype: "gxp_getfeedfeatureinfo"
        }/* - TEMPORARLY DISABLED GXPLORER PLAYBACK - ,{
	          ptype: "gxp_playback",
	          outputTarget: "paneltbar"
        }*/);
        GeoNode.Composer.superclass.loadConfig.apply(this, arguments);
        for (key in this.tools) {
            var tool = this.tools[key];
            if (tool.id === "featuremanager") {
                tool.on("layerchange", function(mgr, layer, schema) {
                    this.checkLayerPermissions(layer, 'layers');
                }, this);
                break;
            }
        }
    }

});

if (GeoNode.Composer) {
    Ext.override(GeoNode.Composer, GeoNode.ComposerMixin);
}

/** api: constructor
 *  .. class:: Viewer(config)
 *
 *    The GeoNode Viewer application class.
 *    Changes compared to out-of-the-box GeoExplorer:
 *    - loadConfig: TODO
 */
GeoNode.Viewer = window.GeoExplorer && Ext.extend(GeoExplorer.Viewer, {

    /** api: method[loadConfig]
     *  :arg config: ``Object`` The config object passed to the constructor.
     *
     *  Subclasses that load config asynchronously can override this to load
     *  any configuration before applyConfig is called.
     */
     loadConfig: function(config) {
         //Strip custom ptype
         var sources = config.sources;
         for(var key in sources) {
             if( sources[key].ptype && sources[key].ptype.match(/^gn_custom*/)) {
                 delete config.sources[key];
                 var layers = config.map && config.map.layers || [];
                 var newLayers = [];
                 for(var i = 0; i < layers.length; i++) {
                     if(layers[i].source != key) {
                         newLayers.push(layers[i]);
                     }

                 }

                 config.map.layers = newLayers;
             }
         }
         for (var i=0, ii=config.viewerTools.length; i<ii; i++) {
            if (config.viewerTools[i].ptype === "gxp_styler") {
                config.viewerTools[i].rasterStyling = true;
            }
            if (config.viewerTools[i].ptype === "gxp_addlayers") {
                config.viewerTools[i].search = {
                  selectedSource: 'search'
                };
                config.viewerTools[i].catalogSourceKey = catalogSourceKey;
                config.viewerTools[i].feeds = true;
            }
            if (config.viewerTools[i].ptype === "gxp_print") {
                config.viewerTools[i].includeLegend = true;
                config.viewerTools[i].showButtonText = true;
            }
            if (config.viewerTools[i].ptype === "gxp_legend") {
                config.viewerTools[i].autoActivate = true;
            }
        }

         var mapUrl = window.location.hash.substr(1);
         var match = mapUrl.match(/^maps\/(\d+)$/);
         if (match) {
             this.id = Number(match[1]);
             OpenLayers.Request.GET({
                 url: "../" + mapUrl,
                 success: function(request) {
                     var addConfig = Ext.util.JSON.decode(request.responseText);
                     // Don't use persisted tool configurations from old maps
                     delete addConfig.tools;
                     this.applyConfig(Ext.applyIf(addConfig, config));
                 },
                 failure: function(request) {
                     var obj;
                     try {
                         obj = Ext.util.JSON.decode(request.responseText);
                     } catch (err) {
                         // pass
                     }
                     var msg = this.loadConfigErrorText;
                     if (obj && obj.error) {
                         msg += obj.error;
                     } else {
                         msg += this.loadConfigErrorDefaultText;
                     }
                     this.on({
                         ready: function() {
                             this.displayXHRTrouble(msg, request.status);
                         },
                         scope: this
                     });
                     delete this.id;
                     window.location.hash = "";
                     this.applyConfig(config);
                 },
                 scope: this
             });
         } else {
             var query = Ext.urlDecode(document.location.search.substr(1));
             if (query) {
                 if (query.q) {
                     var queryConfig = Ext.util.JSON.decode(query.q);
                     Ext.apply(config, queryConfig);
                 }
                 /**
                  * Special handling for links from local GeoServer.
                  *
                  * The layers query string value indicates layers to add as
                  * overlays from the local source.
                  *
                  * The bbox query string value indicates the initial extent in
                  * the current map projection.
                  */
                  if (query.layers) {
                      var layers = query.layers.split(/\s*,\s*/);
                      for (var i=0,ii=layers.length; i<ii; ++i) {
                          config.map.layers.push({
                              source: "local",
                              name: layers[i],
                              visibility: true,
                              bbox: query.lazy && query.bbox ? query.bbox.split(",") : undefined
                          });
                      }
                  }
                  if (query.bbox) {
                      delete config.map.zoom;
                      delete config.map.center;
                      config.map.extent = query.bbox.split(/\s*,\s*/);
                  }
                  if (query.lazy && config.sources.local) {
                      config.sources.local.requiredProperties = [];
                  }
             }

             GeoNode.Viewer.superclass.loadConfig.apply(this, arguments);
         }

     }

});

if (GeoNode.Viewer) {
    Ext.override(GeoNode.Viewer);
}
