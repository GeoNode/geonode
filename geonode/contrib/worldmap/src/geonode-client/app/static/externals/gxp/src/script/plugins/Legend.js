/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @requires GeoExt/widgets/LegendPanel.js
 * @requires GeoExt/widgets/WMSLegend.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = Legend
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: Legend(config)
 *
 *    Provides an action to display a legend in a new window.
 */
gxp.plugins.Legend = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_legend */
    ptype: "gxp_legend",
    
    /** api: config[menuText]
     *  ``String``
     *  Text for legend menu item (i18n).
     */
    menuText: "Legend",

    /** api: config[tooltip]
     *  ``String``
     *  Text for legend action tooltip (i18n).
     */
    tooltip: "Show Legend",

    /** api: config[actionTarget]
     *  ``Object`` or ``String`` or ``Array`` Where to place the tool's actions
     *  (e.g. buttons or menus)? Use null as the default since our tool has both 
     *  output and action(s).
     */
    actionTarget: null,
    
    /** private: method[constructor]
     */
    constructor: function(config) {
        gxp.plugins.Legend.superclass.constructor.apply(this, arguments);
        
        if (!this.outputConfig) {
            this.outputConfig = {
                width: 300,
                height: 400
            };
        }
        Ext.applyIf(this.outputConfig, {title: this.menuText});
    },

    /** api: method[addActions]
     */
    addActions: function() {
        var actions = [{
            menuText: this.menuText,
            iconCls: "gxp-icon-legend",
            tooltip: this.tooltip,
            handler: function() {
                this.removeOutput();
                this.addOutput();
            },
            scope: this
        }];
        return gxp.plugins.Legend.superclass.addActions.apply(this, [actions]);
    },

    /** api: method[getLegendPanel]
     *  :returns: ``GeoExt.LegendPanel``
     *
     *  Get the legend panel associated with this legend plugin.
     */
    getLegendPanel: function() {
        return this.output[0];
    },

    /** private: method[addOutput]
     *  :arg config: ``Object``
     */
    addOutput: function(config) {
        return gxp.plugins.Legend.superclass.addOutput.call(this, Ext.apply({
            xtype: 'gx_legendpanel',
            ascending: false,
            border: false,
            hideMode: "offsets",
            layerStore: this.target.mapPanel.layers,
            defaults: {cls: 'gxp-legend-item'}
        }, config));
    }

});

Ext.preg(gxp.plugins.Legend.prototype.ptype, gxp.plugins.Legend);
