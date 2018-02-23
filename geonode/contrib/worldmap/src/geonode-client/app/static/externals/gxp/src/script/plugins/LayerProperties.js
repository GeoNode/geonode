/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = LayerProperties
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: LayerProperties(config)
 *
 *    Plugin for showing the properties of a selected layer from the map.
 */
gxp.plugins.LayerProperties = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_layerproperties */
    ptype: "gxp_layerproperties",
    
    /** api: config[menuText]
     *  ``String``
     *  Text for layer properties menu item (i18n).
     */
    menuText: "Layer Properties",

    /** api: config[toolTip]
     *  ``String``
     *  Text for layer properties action tooltip (i18n).
     */
    toolTip: "Layer Properties",
    
    /** api: config[layerPanelConfig]
     *  ``Object`` Additional configuration options for the layer type specific
     *  properties panels, keyed by xtype, e.g.:
     *
     *  .. code-block:: javascript
     *
     *      layerPanelConfig: {
     *          "gxp_wmslayerpanel": {rasterStyling: true}
     *      }
     */
    
    constructor: function(config) {
        gxp.plugins.LayerProperties.superclass.constructor.apply(this, arguments);
        
        if (!this.outputConfig) {
            this.outputConfig = {
                width: 325,
                autoHeight: true
            };
        }
    },
        
    /** api: method[addActions]
     */
    addActions: function() {
        var actions = gxp.plugins.LayerProperties.superclass.addActions.apply(this, [{
            menuText: this.menuText,
            iconCls: "gxp-icon-layerproperties",
            disabled: true,
            tooltip: this.toolTip,
            handler: function() {
                this.removeOutput();
                this.addOutput();
            },
            scope: this
        }]);
        var layerPropertiesAction = actions[0];

        this.target.on("layerselectionchange", function(record) {
            layerPropertiesAction.setDisabled(
                !record || !record.get("properties")
            );
        }, this);
        return actions;
    },
    
    addOutput: function(config) {
        config = config || {};
        var record = this.target.selectedLayer;
        var origCfg = this.initialConfig.outputConfig || {};
        this.outputConfig.title = origCfg.title ||
            this.menuText + ": " + record.get("title");
        this.outputConfig.shortTitle = record.get("title");
        
        //TODO create generic gxp_layerpanel
        var xtype = record.get("properties") || "gxp_layerpanel";
        var panelConfig = this.layerPanelConfig;
        if (panelConfig && panelConfig[xtype]) {
            Ext.apply(config, panelConfig[xtype]);
        }
        return gxp.plugins.LayerProperties.superclass.addOutput.call(this, Ext.apply({
            xtype: xtype,
            authorized: this.target.isAuthorized(),
            layerRecord: record,
            source: this.target.getSource(record),
            defaults: {
                style: "padding: 10px",
                autoHeight: this.outputConfig.autoHeight
            },
            listeners: {
                added: function(cmp) {
                    if (!this.outputTarget) {
                        cmp.on("afterrender", function() {
                            cmp.ownerCt.ownerCt.center();
                        }, this, {single: true});
                    }
                },
                scope: this
            }
        }, config));
    }
        
});

Ext.preg(gxp.plugins.LayerProperties.prototype.ptype, gxp.plugins.LayerProperties);
