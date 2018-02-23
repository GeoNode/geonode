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
 *  class = ZoomToDataExtent
 */

/** api: (extends)
 *  plugins/ZoomToExtent.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: ZoomToDataExtent(config)
 *
 *    Plugin for zooming to the data extent of a vector layer
 */
gxp.plugins.ZoomToDataExtent = Ext.extend(gxp.plugins.ZoomToExtent, {
    
    /** api: ptype = gxp_zoomtodataextent */
    ptype: "gxp_zoomtodataextent",
    
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
    
    /** api: config[featureManager]
     *  ``String`` id of the :class:`gxp.plugins.FeatureManager` to look for
     *  selected features
     */
    
    /** api: config[closest]
     *  ``Boolean`` Find the zoom level that most closely fits the specified
     *  extent. Note that this may result in a zoom that does not exactly
     *  contain the entire extent.  Default is false.
     */
    closest: false,

    /** private: property[iconCls]
     */
    iconCls: "gxp-icon-zoom-to",

    /** api: method[extent]
     */
    extent: function() {
        return this.target.tools[this.featureManager].featureLayer.getDataExtent();
    },

    /** api: method[addActions]
     */
    addActions: function() {
        var actions = gxp.plugins.ZoomToDataExtent.superclass.addActions.apply(this, arguments);
        actions[0].disable();

        var layer = this.target.tools[this.featureManager].featureLayer;
        layer.events.on({
            "featuresadded": function() {
                actions[0].isDisabled() && actions[0].enable();
            },
            "featuresremoved": function() {
                layer.features.length == 0 && actions[0].disable();
            }
        });
        
        return actions;
    }
        
});

Ext.preg(gxp.plugins.ZoomToDataExtent.prototype.ptype, gxp.plugins.ZoomToDataExtent);
