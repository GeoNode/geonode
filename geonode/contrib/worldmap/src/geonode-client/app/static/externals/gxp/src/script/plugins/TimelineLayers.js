/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @requires menu/TimelineMenu.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = TimelineLayers
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: TimelineLayers(config)
 *
 *    Plugin for changing the visibility and title attribute of layers in 
 *    the Timeline.
 */
gxp.plugins.TimelineLayers = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_timelinelayers */
    ptype: "gxp_timelinelayers",
    
    /** api: config[menuText]
     *  ``String``
     *  Text for menu item (i18n).
     */
    menuText: "Layers",

    /** api: method[addActions]
     */
    addActions: function() {
        var timelineTool = this.target.tools[this.timelineTool];
        var actions = gxp.plugins.TimelineLayers.superclass.addActions.apply(this, [{
            text: this.menuText,
            iconCls: "gxp-icon-layer-switcher",
            menu: new gxp.menu.TimelineMenu({
                layers: this.target.mapPanel.layers,
                timelineTool: timelineTool
            })
        }]);
        return actions;
    }
        
});

Ext.preg(gxp.plugins.TimelineLayers.prototype.ptype, gxp.plugins.TimelineLayers);
