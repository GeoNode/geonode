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
 *  class = ZoomToExtent
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: ZoomToExtent(config)
 *
 *    Provides an action for zooming to an extent.  If not configured with a 
 *    specific extent, the action will zoom to the map's visible extent.
 */
gxp.plugins.ZoomToExtent = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_zoomtoextent */
    ptype: "gxp_zoomtoextent",
    
    /** api: config[buttonText]
     *  ``String`` Text to show next to the zoom button
     */
     
    /** api: config[menuText]
     *  ``String``
     *  Text for zoom menu item (i18n).
     */
    menuText: "Zoom To Max Extent",

    /** api: config[tooltip]
     *  ``String``
     *  Text for zoom action tooltip (i18n).
     */
    tooltip: "Zoom To Max Extent",
    
    /** api: config[extent]
     *  ``Array | OpenLayers.Bounds``
     *  The target extent.  If none is provided, the map's visible extent will 
     *  be used.
     */
    extent: null,
    
    /** api: config[closest]
     *  ``Boolean`` Find the zoom level that most closely fits the specified
     *  extent. Note that this may result in a zoom that does not exactly
     *  contain the entire extent.  Default is true.
     */
    closest: true,
    
    /** private: property[iconCls]
     */
    iconCls: "gxp-icon-zoomtoextent",
    
    /** api: config[closest]
     *  ``Boolean`` Find the zoom level that most closely fits the specified
     *  extent. Note that this may result in a zoom that does not exactly
     *  contain the entire extent.  Default is true.
     */
    closest: true,
    
    /** private: method[constructor]
     */
    constructor: function(config) {
        gxp.plugins.ZoomToExtent.superclass.constructor.apply(this, arguments);
        if (this.extent instanceof Array) {
            this.extent = OpenLayers.Bounds.fromArray(this.extent);
        }
    },

    /** api: method[addActions]
     */
    addActions: function() {
        return gxp.plugins.ZoomToExtent.superclass.addActions.apply(this, [{
            text: this.buttonText,
            menuText: this.menuText,
            iconCls: this.iconCls,
            tooltip: this.tooltip,
            handler: function() {
                var map = this.target.mapPanel.map;
                var extent = typeof this.extent == "function" ? this.extent() : this.extent;
                if (!extent) {
                    // determine visible extent
                    var layer, extended;
                    for (var i=0, len=map.layers.length; i<len; ++i) {
                        layer = map.layers[i];
                        if (layer.getVisibility()) {
                            extended = layer.restrictedExtent || layer.maxExtent;
                            if (extent) {
                                extent.extend(extended);
                            } else if (extended) {
                                extent = extended.clone();
                            }
                        }
                    }
                }
                if (extent) {
                    // respect map properties
                    var restricted = map.restrictedExtent || map.maxExtent;
                    if (restricted) {
                        extent = new OpenLayers.Bounds(
                            Math.max(extent.left, restricted.left),
                            Math.max(extent.bottom, restricted.bottom),
                            Math.min(extent.right, restricted.right),
                            Math.min(extent.top, restricted.top)
                        );
                    }
                    map.zoomToExtent(extent, this.closest);
                }
            },
            scope: this
        }]);
    }
        
});

Ext.preg(gxp.plugins.ZoomToExtent.prototype.ptype, gxp.plugins.ZoomToExtent);
