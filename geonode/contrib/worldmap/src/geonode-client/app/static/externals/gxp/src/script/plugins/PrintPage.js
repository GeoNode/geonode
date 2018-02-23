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
gxp.plugins.PrintPage = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_print */
    ptype: "gxp_printpage",
    
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
    
    iconCls: "gxp-icon-print",

    
    /** private: method[constructor]
     */
    constructor: function(config) {
        gxp.plugins.PrintPage.superclass.constructor.apply(this, arguments);
    },
    
    /** api: method[addActions]
     */
    addActions: function() {
        var actions = gxp.plugins.PrintPage.superclass.addActions.call(this, [{
            menuText: this.menuText,
            buttonText: this.buttonText,
            title: this.buttonText,
            text: this.buttonText,
            tooltip: this.tooltip,
            iconCls: this.iconCls,
            text: this.text,
            handler: function() {
            	window.open("/maps/print", 'Print');
            },
            scope: this
        }]);    
        return actions;
    }
});

Ext.preg(gxp.plugins.PrintPage.prototype.ptype, gxp.plugins.PrintPage);