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
gxp.plugins.AddCategory = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gxp_addcategory */
    ptype:"gxp_addcategory",

    /** api: config[addCategoryMenuText]
     *  ``String``
     *  Text for Add Category menu item (i18n).
     */
    addCategoryMenuText:"Add Category",

    /** api: config[addCategoryActionTipText]
     *  ``String``
     *  Text for add category action tooltip (i18n).
     */
    addCategoryActionTipText:"Add a category to the layer tree",

    /** api: config[addCategoryTip]
     *  ``String``
     *  Text for add category action tooltip (i18n).
     */    
    categoryNameText: "Category name:",

    /** api: method[addActions]
     */
    addActions:function () {
        var actions = gxp.plugins.AddCategory.superclass.addActions.apply(this, [
            {
                menuText:this.addCategoryMenuText,
                iconCls:"icon-add",
                disabled:false,
                folderAction: true,
                tooltip:this.addCategoryActionTipText,
                handler:function () {
                    var tree = this.target.layerTree;
                    Ext.MessageBox.prompt(this.addCategoryMenuText, this.categoryNameText, function (btn, text) {
                        if (btn == 'ok') {
                            tree.addCategoryFolder({"group":text}, true);
                        }
                    });
                },
                scope:this
            }
        ]);
       return actions[0];
    }
});

Ext.preg(gxp.plugins.AddCategory.prototype.ptype, gxp.plugins.AddCategory);