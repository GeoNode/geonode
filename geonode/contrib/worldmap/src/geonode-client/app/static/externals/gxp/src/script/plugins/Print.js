/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @requires GeoExt/data/PrintProvider.js
 * @requires GeoExt/widgets/PrintMapPanel.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = Print
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: Print(config)
 *
 *    Provides an action to print the map. Requires GeoExt.ux.PrintPreview,
 *    which is currently mirrored at git://github.com/GeoNode/PrintPreview.git.
 */
gxp.plugins.Print = Ext.extend(gxp.plugins.Tool, {
    
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

    iconCls: "gxp-icon-print",

    text: null,

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
                            if (output && output[0]) {
                                output[0].getRootNode().cascade(function(node) {
                                    if (node.component && !node.component.hidden) {
                                        var cmp = node.component;
                                        var encFn = this.encoders.legends[cmp.getXType()];
                                        encodedLegends = encodedLegends.concat(
                                            encFn.call(this, cmp, jsonData.pages[0].scale));
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
                iconCls: this.iconCls,
                text: this.text,
                disabled: this.printCapabilities !== null ? false : true,
                handler: function() {
                    var supported = getSupportedLayers();
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
            function getSupportedLayers() {
                var supported = [];
                mapPanel.layers.each(function(record) {
                    var layer = record.getLayer();
                    if (isSupported(layer)) {
                        supported.push(layer);
                    }
                });
                return supported;
            }

            function isSupported(layer) {
                return (
                    layer instanceof OpenLayers.Layer.WMS ||
                    layer instanceof OpenLayers.Layer.OSM
                );
            }

            function createPrintWindow() {
                var legend = null;
                if (this.includeLegend === true) {
                    var key, tool;
                    for (key in this.target.tools) {
                        tool = this.target.tools[key];
                        if (tool.ptype === "gxp_legend") {
                            legend = tool.getLegendPanel();
                            break;
                        }
                    }
                    // if not found, look for a layer manager instead
                    if (legend === null) {
                        for (key in this.target.tools) {
                            tool = this.target.tools[key];
                            if (tool.ptype === "gxp_layermanager") {
                                legend = tool;
                                break;
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
                                            return isSupported(evt.layer);
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

Ext.preg(gxp.plugins.Print.prototype.ptype, gxp.plugins.Print);
