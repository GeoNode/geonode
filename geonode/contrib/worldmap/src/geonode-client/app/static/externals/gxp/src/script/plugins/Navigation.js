/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @requires OpenLayers/Kinetic.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = Navigation
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: Navigation(config)
 *
 *    Provides one action for panning the map and zooming in with
 *    a box. Optionally provide mousewheel zoom support.
 */
gxp.plugins.Navigation = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_navigation */
    ptype: "gxp_navigation",
    
    /** api: config[menuText]
     *  ``String``
     *  Text for navigation menu item (i18n).
     */
    menuText: "Pan Map",

    /** api: config[tooltip]
     *  ``String``
     *  Text for navigation action tooltip (i18n).
     */
    tooltip: "Pan Map",

    /** private: method[constructor]
     */
    constructor: function(config) {
        gxp.plugins.Navigation.superclass.constructor.apply(this, arguments);
    },

    /** api: method[addActions]
     */
    addActions: function() {
        var control;
        // If no controlOptions are configured, try to find a Navigation
        // control on the target map.
        if (!this.controlOptions) {
            candidates = this.target.mapPanel.map.getControlsByClass('OpenLayers.Control.Navigation');
            if (candidates.length) {
                control = candidates[0];
            }
        } else {
            this.controlOptions = this.controlOptions || {};
            Ext.applyIf(this.controlOptions, {dragPanOptions: {enableKinetic: true}});
            control = new OpenLayers.Control.Navigation(this.controlOptions);
        }
        var actions = [new GeoExt.Action({
            tooltip: this.tooltip,
            menuText: this.menuText,
            iconCls: "gxp-icon-pan",
            enableToggle: true,
            pressed: true,
            allowDepress: false,
            control: control,
            map: control.map ? null : this.target.mapPanel.map,
            toggleGroup: this.toggleGroup
        })];
        return gxp.plugins.Navigation.superclass.addActions.apply(this, [actions]);
    }
        
});

Ext.preg(gxp.plugins.Navigation.prototype.ptype, gxp.plugins.Navigation);
