/**
 * Copyright (c) 2012-2012 OpenGeo
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires GeoExplorer/GeonodePrintProvider.js
 * @requires GeoExplorer/GeonodePrintPanel.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = GeoExplorer.PrintPanel
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("GeoExplorer");

/** api: constructor
 *  .. class:: PrintPlugin(config)
 *
 *    Provides an action to print the map
 */
GeoExplorer.PrintPlugin = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gn_print */
    ptype: "gn_print",

    /** api: config[printService]
     *  ``String``
     *  URL of the GeoNode print service.
     *  Defaults to '/printing/print/'
     */
    printService: '/printing/print/',

    /** api: config[templateService]
     *  ``String``
     *  URL of the GeoNode print template source.
     *  Do NOT include a trailing slash
     *  Defaults to 'printing/templates'
     */
    templateService: '/printing/templates',

    /** api: config[previewService]
     *  ``String``
     *  URL of the GeoNode print preview service.
     *  Defaults to 'printing/preview/'
     */
    previewService: '/printing/preview/',

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

    printProvider: null,

    /** api: method[addActions]
     */
    addActions: function() {
        // look for the legend
        var legend;
        for (var key in this.target.tools) {
            var tool = this.target.tools[key];
            if (tool.ptype === "gxp_layermanager") {
                legend = tool;
            }
            if (tool.ptype === "gxp_legend") {
                legend = tool;
            }
        }
        // don't add any action if there is no print service configured
        if(this.printService !== null) {
            var provider = new GeoExplorer.GeonodePrintProvider(Ext.apply({
                legend: legend,
                printService: this.printService,
                templateService: this.templateService,
                previewService: this.previewService
            }, this.initialConfig.controlConfig));
            this.printProvider = provider;
            var actions = [{
                menuText: this.menuText,
                buttonText: this.buttonText,
                tooltip: this.tooltip,
                disabled: !this.target.id,
                iconCls: "gxp-icon-print",
                scope: this
            }];
            this.outputAction = 0;
            if(!this.outputTarget) {this.outputTarget = this.target.mapPanel.id;}
            this.target.on("save", function() {
                actions[0].setDisabled(false);
            }, null, {single: true});
            GeoExplorer.PrintPlugin.superclass.addActions.call(this, actions);
        }

    },
    addOutput: function(config) {
        var winHeight = parseInt(this.target.mapPanel.getHeight() * 0.75, 10);
        config = Ext.applyIf(config || {}, {
            title: this.menuText,
            modal: true,
            border: false,
            layout: 'fit',
            width: 650,
            height: winHeight,
            xtype: 'window'
        });
        this.outputConfig = this.outputConfig ? Ext.apply(this.outputConfig, config) : config;

        Ext.apply(this.outputConfig, {
            items:[{
                xtype: 'gn_printpanel',
                printProvider: this.printProvider,
                map: this.target.mapPanel,
                mapId: this.target.id,
                localGeoServerBaseUrl: this.target.localGeoServerBaseUrl
            }]
        });
        var output = Ext.create(this.outputConfig);
        GeoExplorer.PrintPlugin.superclass.addOutput.apply(this, [output]);
    }
});

Ext.preg(GeoExplorer.PrintPlugin.prototype.ptype, GeoExplorer.PrintPlugin);
