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
gxp.plugins.LayerShare = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gxp_sharelayer */
    ptype: "gxp_layershare",

    /** api: config[menuText]
     *  ``String``
     *  Text for layer share menu item (i18n).
     */
    menuText: "Share Layer",

    /** api: config[toolTip]
     *  ``String``
     *  Text for layer share action tooltip (i18n).
     */
    toolTip: "Layer info and download links",

    linkPrefix: "/data/",

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
        var actions = gxp.plugins.LayerShare.superclass.addActions.apply(this, [{
            menuText: this.menuText,
            iconCls: "gxp-icon-link",
            disabled: false,
            tooltip: this.toolTip,
            handler: function() {
                this.removeOutput();
                this.addOutput();
            },
            scope: this
        }]);
        var layerShareAction = actions[0];

        this.target.on("layerselectionchange", function(record) {

            if (!layerShareAction.isDisabled() && record && record.get('group') !== 'background') {
                this.link = record.get('detail_url') || this.linkPrefix + record.getLayer().params.LAYERS;
            }

        }, this);
        return actions;
    },

    addOutput: function(config) {
        window.open(this.link);
    }

});

Ext.preg(gxp.plugins.LayerShare.prototype.ptype, gxp.plugins.LayerShare);
