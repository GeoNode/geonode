/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @require OpenLayers/Control/ZoomBox.js
 * @require GeoExt/widgets/Action.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = Zoom
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: Zoom(config)
 *
 *    Provides actions for box zooming, zooming in and zooming out.
 */
gxp.plugins.Zoom = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_zoom */
    ptype: "gxp_zoom",
    
    /** api: config[zoomMenuText]
     *  ``String``
     *  Text for zoom box menu item (i18n).
     */
    zoomMenuText: "Zoom Box",

    /** api: config[zoomInMenuText]
     *  ``String``
     *  Text for zoom in menu item (i18n).
     */
    zoomInMenuText: "Zoom In",

    /** api: config[zoomOutMenuText]
     *  ``String``
     *  Text for zoom out menu item (i18n).
     */
    zoomOutMenuText: "Zoom Out",

    /** api: config[zoomInTooltip]
     *  ``String``
     *  Text for zoom box action tooltip (i18n).
     */
    zoomTooltip: "Zoom by dragging a box",

    /** api: config[zoomInTooltip]
     *  ``String``
     *  Text for zoom in action tooltip (i18n).
     */
    zoomInTooltip: "Zoom in",

    /** api: config[zoomOutTooltip]
     *  ``String``
     *  Text for zoom out action tooltip (i18n).
     */
    zoomOutTooltip: "Zoom out",
    
    /** api: config[toggleGroup]
     *  ``String`` Toggle group for this plugin's Zoom action.
     */
    
    /** api: config[showZoomBoxAction]
     * {Boolean} If true, the tool will have a Zoom Box button as first action.
     * The zoom box will be provided by an OpenLayers.Control.ZoomBox, and
     * :obj:`controlOptions` configured for this tool will apply to the ZoomBox
     * control.
     * If set to false, only Zoom In and Zoom Out buttons will be created.
     * Default is false.
     */

    /** private: method[constructor]
     */
    constructor: function(config) {
        gxp.plugins.Zoom.superclass.constructor.apply(this, arguments);
    },

    /** api: method[addActions]
     */
    addActions: function() {
        var actions = [{
            menuText: this.zoomInMenuText,
            iconCls: "gxp-icon-zoom-in",
            tooltip: this.zoomInTooltip,
            handler: function() {
                this.target.mapPanel.map.zoomIn();    
            },
            scope: this
        }, {
            menuText: this.zoomOutMenuText,
            iconCls: "gxp-icon-zoom-out",
            tooltip: this.zoomOutTooltip,
            handler: function() {
                this.target.mapPanel.map.zoomOut();
            },
            scope: this
        }];
        if (this.showZoomBoxAction) {
            actions.unshift(new GeoExt.Action({
                menuText: this.zoomText,
                iconCls: "gxp-icon-zoom",
                tooltip: this.zoomTooltip,
                control: new OpenLayers.Control.ZoomBox(this.controlOptions),
                map: this.target.mapPanel.map,
                enableToggle: true,
                allowDepress: false,
                toggleGroup: this.toggleGroup
            }));
        }
        return gxp.plugins.Zoom.superclass.addActions.apply(this, [actions]);
    }
        
});

Ext.preg(gxp.plugins.Zoom.prototype.ptype, gxp.plugins.Zoom);
