/**
 * Published under the GNU General Public License.
 * Copyright 2011-2012 © The President and Fellows of Harvard College
 */
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
gxp.plugins.MapShare = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gxp_sharelayer */
    ptype: "gxp_mapshare",

    /** api: config[text]
     *  ``String``
     *  Text for layer share menu item (i18n).
     */
    text: "Share My Map",

    /** api: config[toolTip]
     *  ``String``
     *  Text for layer share action tooltip (i18n).
     */
    toolTip: "Map info and download links",

    linkPrefix: "/maps/",

    linkSuffix: "/view",

    iconCls: "gxp-icon-link",

    /** api: method[addActions]
     */
    addActions: function() {
      // var link = this.linkPrefix + this.target.mapID + this.linkSuffix;
      var link = this.linkPrefix + this.target.mapID;
        var actions = gxp.plugins.MapShare.superclass.addActions.call(this, [{
            iconCls: this.iconCls,
            text: this.text,
            tooltip: this.toolTip,
            disabled: this.target.mapID == null,
            handler: function() {
                window.open(link);
            },
            scope: this
        }]);

        return actions;
    }

});

Ext.preg(gxp.plugins.MapShare.prototype.ptype, gxp.plugins.MapShare);
