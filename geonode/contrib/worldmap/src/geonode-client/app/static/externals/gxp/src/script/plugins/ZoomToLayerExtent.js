/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/ZoomToExtent.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = ZoomToLayerExtent
 */

/** api: (extends)
 *  plugins/ZoomToExtent.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: ZoomToLayerExtent(config)
 *
 *    Plugin for zooming to the extent of a non-vector layer
 */
gxp.plugins.ZoomToLayerExtent = Ext.extend(gxp.plugins.ZoomToExtent, {
    
    /** api: ptype = gxp_zoomtolayerextent */
    ptype: "gxp_zoomtolayerextent",
    
    /** api: config[menuText]
     *  ``String``
     *  Text for zoom menu item (i18n).
     */
    menuText: "Zoom to layer extent",

    /** api: config[tooltip]
     *  ``String``
     *  Text for zoom action tooltip (i18n).
     */
    tooltip: "Zoom to layer extent",
    
    /** private: property[iconCls]
     */
    iconCls: "gxp-icon-zoom-to",

    /** private: method[destroy]
     */
    destroy: function() {
        this.selectedRecord = null;
        gxp.plugins.ZoomToLayerExtent.superclass.destroy.apply(this, arguments);
    },

    /** api: method[extent]
     */
    extent: function() {
        var layer = this.selectedRecord.getLayer(),
            dataExtent;
        if (OpenLayers.Layer.Vector) {
            dataExtent = layer instanceof OpenLayers.Layer.Vector &&
                layer.getDataExtent();
        }
        return layer.restrictedExtent || dataExtent || layer.maxExtent || map.maxExtent;
    },

    /** api: method[addActions]
     */
    addActions: function() {
        var actions = gxp.plugins.ZoomToLayerExtent.superclass.addActions.apply(this, arguments);
        actions[0].disable();

        this.target.on("layerselectionchange", function(record) {
            this.selectedRecord = record;
            actions[0].setDisabled(
                !record || !record.get('layer')
            );
        }, this);

        return actions;
    }
        
});

Ext.preg(gxp.plugins.ZoomToLayerExtent.prototype.ptype, gxp.plugins.ZoomToLayerExtent);
