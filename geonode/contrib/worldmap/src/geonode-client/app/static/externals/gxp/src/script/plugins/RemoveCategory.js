/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * requires plugins/Tool.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = AddCategory
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
gxp.plugins.RemoveCategory = Ext.extend(gxp.plugins.Tool, {
	
    /** api: ptype = gxp_addcategory */
    ptype:"gxp_removecategory",

    /** api: config[removeCategoryActionText]
     *  ``String``
     *  Text for remove Category menu item (i18n).
     */
    removeCategoryActionText:"Remove Category",

    /** api: config[removeCategoryActionTipText]
     *  ``String``
     *  Text for remove category action tooltip (i18n).
     */
    removeCategoryActionTipText: "Remove this category and all its layers from the map",

    /** api: config[cannotRemoveText]
     *  ``String``
     *  Text for cannot remove category message (i18n).
     */    
    cannotRemoveText: "This category cannot be removed",

    
    /** api: method[getRecordFromNode]
     */
    getRecordFromNode:  function(node) {
        var record;
        if (node && node.layer) {
            var layer = node.layer;
            var store = node.layerStore;
            record = store.getAt(store.findBy(function(r) {
                return r.getLayer() === layer;
            }));
        }
        return record;
    },
    
    /** api: method[removeNode]
     */
    removeNode: function (node) {
    	Ext.Msg.show({
    		title: this.removeCategoryActionText,
    		msg: this.removeCategoryActionTipText,
    		buttons: Ext.Msg.OKCANCEL,
    		fn: function (btn) {
                if (btn == 'ok') {
                    if (node.parentNode.isRoot) {
                        Ext.Msg.alert(this.layerContainerText, this.cannotRemoveText);
                        return false;
                    }
                    if (node) {
                        while (node.childNodes.length > 0) {
                            var record = this.getRecordFromNode(node.childNodes[0]);
                            if (record) {
                                this.target.removeFromSelectControl(record);
                                this.target.mapPanel.layers.remove(record, true);
                            }
                        }

                        var parentNode = node.parentNode;
                        parentNode.removeChild(node, true);
                    }
                }
    		},
    		scope: this
    	});
    },
    
    /** api: method[addActions]
     */
    addActions:function () {

        var actions = gxp.plugins.RemoveCategory.superclass.addActions.apply(this, [
            {
                menuText:this.removeCategoryActionText,
                iconCls: "gxp-icon-removelayers",
                disabled:false,
                folderAction: true,
                tooltip:this.removeCategoryActionTipText,
                handler: function(action) {
                    this.removeNode(action.selectedNode);
                },
                scope:this
            }
        ]);

        return actions[0];
    }
});

Ext.preg(gxp.plugins.RemoveCategory.prototype.ptype, gxp.plugins.RemoveCategory);