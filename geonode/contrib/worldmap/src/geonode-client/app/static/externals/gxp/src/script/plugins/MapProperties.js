/**
 * Copyright (c) 2008-2012 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @requires widgets/form/ColorField.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = MapProperties
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: MapProperties(config)
 *
 *    Plugin for showing the properties of the map.
 */
gxp.plugins.MapProperties = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gxp_mapproperties */
    ptype: "gxp_mapproperties",

    /** api: config[colorManager]
     *  ``Function``
     *  Optional color manager constructor to be used as a plugin for the color
     *  field.
     */
    colorManager: null,

    /** api: config[menuText]
     *  ``String``
     *  Text for map properties menu item (i18n).
     */
    menuText: "Map Properties",

    /** api: config[toolTip]
     *  ``String``
     *  Text for map properties action tooltip (i18n).
     */
    toolTip: "Map Properties",

    /* i18n */
    wrapDateLineText: "Wrap dateline",
    numberOfZoomLevelsText: "Number of zoom levels",
    colorText: "Background color",

    addActions: function() {
        var baseLayer = this.target.mapPanel.map.baseLayer;
        var container = Ext.get(this.target.mapPanel.map.getViewport());
        if (this.initialConfig.backgroundColor) {
            container.setStyle('background-color', this.initialConfig.backgroundColor);
        }
        if (this.initialConfig.numZoomLevels) {
            baseLayer.addOptions({numZoomLevels: this.initialConfig.numZoomLevels});
            this.target.mapPanel.map.events.triggerEvent('changebaselayer', {layer: baseLayer});
        }
        if (this.initialConfig.wrapDateLine) {
            baseLayer.wrapDateLine = this.initialConfig.wrapDateLine;
        }
        return gxp.plugins.MapProperties.superclass.addActions.apply(this, [{
            menuText: this.menuText,
            iconCls: "gxp-icon-mapproperties",
            tooltip: this.toolTip,
            handler: function() {
                this.removeOutput();
                this.addOutput();
            },
            scope: this
        }]);
    },

    addOutput: function() {
        var colorFieldPlugins;
        if (this.colorManager) {
            colorFieldPlugins = [new this.colorManager()];
        }
        var baseLayer = this.target.mapPanel.map.baseLayer;
        var container = Ext.get(this.target.mapPanel.map.getViewport());
        return gxp.plugins.MapProperties.superclass.addOutput.call(this, {
            xtype: 'form',
            border: false,
            bodyStyle: "padding: 10px",
            items: [{
                xtype: 'numberfield',
                allowNegative: false,
                allowDecimals: false,
                fieldLabel: this.numberOfZoomLevelsText,
                minValue: 1,
                value: baseLayer.numZoomLevels,
                listeners: {
                    "change": function(fld, value) {
                        baseLayer.addOptions({numZoomLevels: value});
                        this.target.mapPanel.map.events.triggerEvent('changebaselayer', {layer: baseLayer});
                    },
                    scope: this
                }
            }, {
                xtype: 'checkbox',
                fieldLabel: this.wrapDateLineText,
                checked: baseLayer.wrapDateLine,
                listeners: {
                    "check": function(cb, value) {
                        baseLayer.wrapDateLine = value;
                    },
                    scope: this
                }
            }, {
                xtype: "gxp_colorfield",
                fieldLabel: this.colorText,
                value: container.getColor('background-color'),
                plugins: colorFieldPlugins,
                listeners: {
                    valid: function(field) {
                        container.setStyle('background-color', field.getValue());
                    },
                    scope: this
                }
            }]
        });
    },

    /** api: method[getState]
     *  :return {Object}
     *  Gets the configured tool state.
     */
    getState: function(){
        var baseLayer = this.target.mapPanel.map.baseLayer;
        var container = Ext.get(this.target.mapPanel.map.getViewport());
        return {
            ptype: this.ptype,
            backgroundColor : container.getColor('background-color'),
            numZoomLevels : baseLayer.numZoomLevels,
            wrapDateLine : baseLayer.wrapDateLine
        };
    }
});

Ext.preg(gxp.plugins.MapProperties.prototype.ptype, gxp.plugins.MapProperties);
