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
 *  class = RemoveLayer
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: RemoveLayer(config)
 *
 *    Plugin for removing a selected layer from the map.
 *    TODO Make this plural - selected layers
 */
gxp.plugins.RemoveLayer = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_removelayer */
    ptype: "gxp_removelayer",
    
    /** api: config[removeMenuText]
     *  ``String``
     *  Text for remove menu item (i18n).
     */
    removeMenuText: "Remove layer",

    /** api: config[removeActionTip]
     *  ``String``
     *  Text for remove action tooltip (i18n).
     */
    removeActionTip: "Remove layer",
    
    /** api: method[addActions]
     */
    addActions: function() {
        var selectedLayer;
        var actions = gxp.plugins.RemoveLayer.superclass.addActions.apply(this, [{
            menuText: this.removeMenuText,
            iconCls: "gxp-icon-removelayers",
            disabled: true,
            tooltip: this.removeActionTip,
            handler: function() {
                var record = selectedLayer;
                if(record) {
                    this.target.mapPanel.layers.remove(record);
                }
            },
            scope: this
        }]);
        var removeLayerAction = actions[0];

        this.target.on("layerselectionchange", function(record) {
            selectedLayer = record;
            removeLayerAction.setDisabled(
                this.target.mapPanel.layers.getCount() <= 1 || !record
            );
        }, this);
        var enforceOne = function(store) {
            removeLayerAction.setDisabled(
                !selectedLayer || store.getCount() <= 1
            );
        };
        this.target.mapPanel.layers.on({
            "add": enforceOne,
            "remove": enforceOne
        });
        
        return actions;
    }
        
});

Ext.preg(gxp.plugins.RemoveLayer.prototype.ptype, gxp.plugins.RemoveLayer);
