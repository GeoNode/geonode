/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @requires OpenLayers/Control/NavigationHistory.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = NavigationHistory
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: NavigationHistory(config)
 *
 *    Provides two actions for zooming back and forth.
 */
gxp.plugins.NavigationHistory = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_navigationhistory */
    ptype: "gxp_navigationhistory",
    
    /** api: config[previousMenuText]
     *  ``String``
     *  Text for zoom previous menu item (i18n).
     */
    previousMenuText: "Zoom To Previous Extent",

    /** api: config[nextMenuText]
     *  ``String``
     *  Text for zoom next menu item (i18n).
     */
    nextMenuText: "Zoom To Next Extent",

    /** api: config[previousTooltip]
     *  ``String``
     *  Text for zoom previous action tooltip (i18n).
     */
    previousTooltip: "Zoom To Previous Extent",

    /** api: config[nextTooltip]
     *  ``String``
     *  Text for zoom next action tooltip (i18n).
     */
    nextTooltip: "Zoom To Next Extent",
    
    /** private: method[constructor]
     */
    constructor: function(config) {
        gxp.plugins.NavigationHistory.superclass.constructor.apply(this, arguments);
    },

    /** api: method[addActions]
     */
    addActions: function() {
        var historyControl = new OpenLayers.Control.NavigationHistory();
        this.target.mapPanel.map.addControl(historyControl);
        var actions = [new GeoExt.Action({
            menuText: this.previousMenuText,
            iconCls: "gxp-icon-zoom-previous",
            tooltip: this.previousTooltip,
            disabled: true,
            control: historyControl.previous
        }), new GeoExt.Action({
            menuText: this.nextMenuText,
            iconCls: "gxp-icon-zoom-next",
            tooltip: this.nextTooltip,
            disabled: true,
            control: historyControl.next
        })];
        return gxp.plugins.NavigationHistory.superclass.addActions.apply(this, [actions]);
    }
        
});

Ext.preg(gxp.plugins.NavigationHistory.prototype.ptype, gxp.plugins.NavigationHistory);
