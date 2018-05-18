/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @requires GeoExt/widgets/tree/LayerNode.js
 * @requires GeoExt/widgets/tree/TreeNodeUIEventMixin.js
 * @requires GeoExt/widgets/tree/LayerContainer.js
 * @requires GeoExt/widgets/tree/LayerLoader.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = LayerTree
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

Ext.override(Ext.tree.TreeNode, {
    findDescendant: function(attribute, value) {
        var children = this.childNodes;
        for(var i = 0, l = children.length; i < l; i++) {
            if(children[i].attributes[attribute] == value){
                return children[i];
            } else if(node = children[i].findDescendant(attribute, value)) {
                return node;
            }
        }
        return null;
    }
});


/** api: constructor
 *  .. class:: LayerTree(config)
 *
 *    Plugin for adding a tree of layers to a :class:`gxp.Viewer`. Also
 *    provides a context menu on layer nodes.
 */
gxp.plugins.LayerTree = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gxp_layertree */
    ptype: "gxp_layertree",

    /** api: config[shortTitle]
     *  ``String``
     *  Short title text for this plugin's output (i18n)
     */
    shortTitle: "Layers",

    /** api: config[rootNodeText]
     *  ``String``
     *  Text for root node of layer tree (i18n).
     */
    rootNodeText: "Layers",

    /** api: config[overlayNodeText]
     *  ``String``
     *  Text for overlay node of layer tree (i18n).
     */
    overlayNodeText: "Overlays",

    /** api: config[baseNodeText]
     *  ``String``
     *  Text for baselayer node of layer tree (i18n).
     */
    baseNodeText: "Base Layers",

    /** api: config[removeMenuText]
     *  ``String``
     *  Text for remove menu item (i18n).
     */
    addCategoryActionText:"Add Category",

    /** api: config[addCategoryTip]
     *  ``String``
     *  Text for remove action tooltip (i18n).
     */
    addCategoryActionTipText:"Add category",

    /** api: config[groups]
     *  ``Object`` The groups to show in the layer tree. Keys are group names,
     *  and values are either group titles or an object with ``title`` and
     *  ``exclusive`` properties. ``exclusive``, if Boolean, means that nodes
     *  will have radio buttons instead of checkboxes, so only one layer of the
     *  group can be active at a time. If String, ``exclusive`` can be used to
     *  create exclusive sets of layers among several groups, by assigning the
     *  same string to each group. Optional, the default is
     *
     *  .. code-block:: javascript
     *
     *      groups: {
     *          "default": "Overlays", // title can be overridden with overlayNodeText
     *          "background": {
     *              title: "Base Layers", // can be overridden with baseNodeText
     *              exclusive: true
     *          }
     *      }
     */
    groups: null,

    /** api: config[defaultGroup]
     *  ``String`` The name of the default group, i.e. the group that will be
     *  used when none is specified. Defaults to ``default``.
     */
    defaultGroup: "default",

    /** private: config[treeNodeUI]
     *  ``Ext.tree.TreeNodeUI``
     */
    treeNodeUI: null,

    /** private: method[constructor]
     *  :arg config: ``Object``
     */
    constructor: function(config) {
        gxp.plugins.LayerTree.superclass.constructor.apply(this, arguments);
        if (!this.groups) {
            this.groups = [
                {"title": this.baseNodeText, "group": "background", "exclusive": true}
            ];
        } else {
            this.groups.push({"title": this.baseNodeText, "group": "background", "exclusive": true});
        }
        if (!this.treeNodeUI) {
            this.treeNodeUI = Ext.extend(
                GeoExt.tree.LayerNodeUI,
                new GeoExt.tree.TreeNodeUIEventMixin()
            );
        }
    },

    /** private: method[addOutput]
     *  :arg config: ``Object``
     *  :returns: ``Ext.Component``
     */
    addOutput: function(config) {
        config = Ext.apply(this.createOutputConfig(), config || {});
        this.tree = gxp.plugins.LayerTree.superclass.addOutput.call(this, config);
        if (this.tree.body) {
            this.tree.body.on('mouseover', this.onTreeMouseover, this, {delegate: 'a.x-tree-node-anchor'});
        }
        return this.tree;
    },

    /** private: method[createOutputConfig]
     *  :returns: ``Object`` Configuration object for an Ext.tree.TreePanel
     */
    createOutputConfig: function() {
        var treeRoot = new Ext.tree.TreeNode({
            text: this.rootNodeText,
            id: "layertree_overlay_root",
            expanded: true,
            isTarget: false,
            allowDrop: false
        });

        this.overlayRoot = new Ext.tree.TreeNode({
            id: "layertree_overlay_root",
            text: this.overlayNodeText,
            expanded: true,
            isTarget: false,
            allowDrop: true
        });

        treeRoot.appendChild(this.overlayRoot);

        var defaultGroup = this.defaultGroup,
            plugin = this,
            exclusive;

        for (var group = 0, max=this.groups.length; group < max; group++) {
            var newFolder = this.createCategoryFolder(this.groups[group]);
            //for (var group in this.groups) {


            //console.log("Group:" + this.groups[group].group);
            if (this.groups[group].group == "background") {
                //console.log("Append to tree root:" + this.groups[group].group);
                treeRoot.appendChild(newFolder);
            }
            else {
                //console.log("Append to overlay root:" + this.groups[group].group);
                this.overlayRoot.appendChild(newFolder);
            }
            newFolder.enable();
        }

        return {
            xtype: "treepanel",
            id: "layertree_panel",
            root: treeRoot,
            //plugins: new NodeMouseoverPlugin(),
            rootVisible: false,
            shortTitle: this.shortTitle,
            border: false,
            enableDD: true,
            selModel: new Ext.tree.DefaultSelectionModel({
                listeners: {
                    beforeselect: this.handleBeforeSelect,
                    scope: this
                }
            }),
            listeners: {
                contextmenu: this.handleTreeContextMenu,
                beforemovenode: this.handleBeforeMoveNode,
                beforenodedrop: this.handleBeforeNodeDrop,
                movenode: this.handleMoveNode,
                scope: this
            },
            contextMenu: new Ext.menu.Menu({
                items: []
            })
        };
    },

    toggleFolder: function(groupConfig) {
        var expanded = groupConfig["expanded"] ? groupConfig["expanded"] === "true" :  true;
        var groupNode = this.overlayRoot.findChild("text", groupConfig.group)
        if (groupNode != null) {
            switch (expanded) {
                case false:
                    groupNode.collapse();
                default:
                    groupNode.expand();
            }
        }
    },

    addCategoryFolder: function(groupConfig, insert){
        var newFolder = this.createCategoryFolder(groupConfig);
        if (newFolder) {
            if (insert)
                this.overlayRoot.insertBefore(newFolder, this.overlayRoot.firstChild);
            else
                this.overlayRoot.appendChild(newFolder);
        }
    },


    createCategoryFolder: function(groupConfig) {
        if (typeof groupConfig == "string") {
            groupConfig = {"group": groupConfig};
        }
        var expanded = groupConfig["expanded"] ? groupConfig["expanded"] === "true" :  true;
        var group = groupConfig.group;
        if (group == "" || !group)
            group = "General";
        if (this.overlayRoot.findChild("text", group) == null) {
            var defaultGroup = this.defaultGroup,
                plugin = this,
                exclusive = groupConfig.exclusive;
            var newFolder = new GeoExt.tree.LayerContainer({
                text: groupConfig.title || groupConfig.group,
                group:groupConfig.group,
                iconCls: "gxp-folder",
                expanded: expanded,
                loader: new GeoExt.tree.LayerLoader({
                    store: this.target.mapPanel.layers,
                    baseAttrs: exclusive ?
                    {checkedGroup: Ext.isString(exclusive) ? exclusive : groupConfig.group} :
                        undefined,
                    filter: function(record) {
                        return (record.get("group") || defaultGroup) == groupConfig.group &&
                            record.getLayer().displayInLayerSwitcher == true;
                    },
                    createNode: function (attr) {
                        plugin.configureLayerNode(this, attr);
                        return GeoExt.tree.LayerLoader.prototype.createNode.apply(this, arguments);
                    }
                }),
                singleClickExpand: true,
                allowDrag: true,
                enableDD: true,
                listeners: {
                    append: function(tree, node) {
                        node.expand();
                    }
                }
            });

            return newFolder;
        }
    },


    /**
     * Enclose URL's in a string with <a> tags IF there are no <a> tags already present in the string.
     */
    replaceURLWithHTMLLinks: function(text) {
        if (text != null  && !text.match(/\<a|\<img/ig)) {
            var exp = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
            return text.replace(exp,"<a target='_blank' href='$1'>$1</a>");
        }  else
            return text;
    },

    /** private: method[configureLayerNode]
     *  :arg loader: ``GeoExt.tree.LayerLoader``
     *  :arg node: ``Object`` The node
     */
    configureLayerNode: function(loader, attr) {
        attr.uiProvider = this.treeNodeUI;
        var layer = attr.layer;
        var store = attr.layerStore;
        if (layer && store) {
            var record = store.getAt(store.findBy(function(r) {
                return r.getLayer() === layer;
            }));
            if (record) {
                //attr.tiptext = this.replaceURLWithHTMLLinks(record.get('abstract'));
                if (!record.get("queryable")) {
                    attr.iconCls = "gxp-tree-rasterlayer-icon";
                }
                if (record.get("fixed")) {
                    attr.allowDrag = false;
                }
                if (record.get("disabled")) {
                    attr.disabled = true;
                    attr.autoDisable = false;
                }
                attr.listeners = {
                    rendernode: function(node) {
                        if (record === this.target.selectedLayer) {
                            node.select();
                        }
                        this.target.on("layerselectionchange", function(rec) {
                            if (!this.selectionChanging && rec === record) {
                                node.select();
                            }
                        }, this);
                    },
                    scope: this
                };
            }
        }
    },

    /** private: method[handleBeforeSelect]
     */
    handleBeforeSelect: function(selModel, node) {
        var changed = true;
        var layer = node && node.layer;
        var record;
        if (layer) {
            var store = node.layerStore;
            record = store.getAt(store.findBy(function(r) {
                return r.getLayer() === layer;
            }));
        }
        this.selectionChanging = true;
        changed = this.target.selectLayer(record);
        this.selectionChanging = false;
        return changed;
    },

    /** private: method[handleTreeContextMenu]
     *  :arg node: ``Object`` The node
     *  :arg e: The event
     */
    handleTreeContextMenu: function(node, e) {
        function toggleVisibility(item, node) {
            if (item.folderAction != (node.layer ? undefined: true))  {
                item.hide();
            } else {
                item.show();
            }
        }

        if(node) {
            node.select();
            var tree = node.getOwnerTree();
            if (tree.getSelectionModel().getSelectedNode() === node) {
                var c = tree.contextMenu;
                c.contextNode = node;
                c.items.eachKey(function(key,item) {
                    toggleVisibility(item, node);
                    if (item.folderAction) {
                        item.selectedNode = node;
                    }
                });
                c.items.getCount() > 0 && c.showAt(e.getXY());
            }
        }

        //Hide the tooltip if it exists
        if (this.tooltip) {
            this.tooltip.hide();
        }
    },

    /** private: method[handleBeforeMoveNode]
     * change the group when moving to a new container
     */
    handleBeforeMoveNode: function(tree, node, oldParent, newParent, i) {
        // change the group when moving to a new container
        if(node.layer && oldParent !== newParent && newParent.loader) {
            var store = newParent.loader.store;
            var index = store.findBy(function(r) {
                return r.getLayer() === node.layer;
            });
            var record = store.getAt(index);
            record.set("group", newParent.attributes.group);
        }
    },

    /** private: method[handleBeforeNodeDrop]
     * Don't allow node drop on top-level folders
     */
    handleBeforeNodeDrop: function(dropEvent) {
        var source_folder_id = undefined;
        var dest_folder = undefined;

        if (dropEvent.data.node.attributes.iconCls == 'gxp-folder') {
            //alert('gx-folder::' + dropEvent.target.attributes.iconCls + ":" + dropEvent.point + ":" + dropEvent.target.parentNode.text + ":" + dropEvent.target.text);
            if (dropEvent.target.attributes.iconCls != "gxp-folder")
                dropEvent.target = dropEvent.target.parentNode;
            if ((dropEvent.target.attributes.iconCls == 'gxp-folder' && dropEvent.point == "above") || (dropEvent.target.text != "background" && dropEvent.target.attributes.iconCls == 'gxp-folder' && dropEvent.point == "below")) {
                return true;
            } else {
                return false;
            }
        } else {
            if (dropEvent.target.parentNode.attributes.group == "background" || (dropEvent.target.parentNode.id == "layertree_overlay_root" && dropEvent.point != "append"))
                return false;
            else
                return true;
        }

    },

    /** private: method[handleMoveNode]
     * Handle moving of layer nodes from one location to another in the tree
     */
    handleMoveNode : function(tree, node, oldParent, newParent, index) {
        var mpl = this.target.mapPanel.layers;
        var x = 0;
        var layerCount = mpl.getCount() - 1;
        var records = [];

        if (!node.isLeaf()) {
            //mpl.suspendEvents();
            this.overlayRoot.cascade(function(node) {
                if (node.isLeaf() && node.layer) {
                    var layer = node.layer;
                    var store = node.layerStore;
                    var index = store.findBy(function(r) {
                        return r.getLayer() === layer;
                    });
                    record = store.getAt(index);
                    if (
                        record.getLayer().displayInLayerSwitcher == true && record.get("group") != "background" && record.get("order") !== x) {
                        record.set("order", x);

                        try {
                            mpl.remove(record);
                            mpl.insert(layerCount - x, [record]);
                        } catch (e) {
                            if (console) {
                                console.log(e);
                            }
                        }
                    }
                    x++;
                }
            });
        }
    },

    onTreeMouseover: function(e, t) {
        var nodeEl = Ext.fly(t).up('div.x-tree-node-el');
        if (nodeEl) {
            var nodeId = nodeEl.getAttributeNS('ext', 'tree-node-id');
            if (nodeId) {
                var node = this.tree.getNodeById(nodeId);
                if (node.layerStore) {
                    var abstractText = this.replaceURLWithHTMLLinks(node.layerStore.getByLayer(node.layer).get("abstract"));
                    var treemanager = Ext.fly(t).up('div.gxp-layermanager-tree');

                    //Create or update tooltip
                    if (this.tooltip && abstractText) {
                        this.tooltip.initTarget(node);
                        this.tooltip.update(abstractText);
                    } else if (abstractText) {
                        this.tooltip = new Ext.ToolTip({
                            id: 'layer_tooltip',
                            target: node,
                            autoHeight: true,
                            dismissDelay: 0,
                            boxMaxHeight: 500,
                            maxWidth: 500,
                            autoScroll:true,
                            html: abstractText
                        });
                    } else if (this.tooltip) {
                        this.tooltip.hide();
                    }



                    //Set or cancel timeouts for tooltip
                    if (this.tooltip) {
                        this.tooltip.on('show', function(){
                            var timeout;
                            var tooltip = this;

                            treemanager.on('mouseleave', function(){
                                timeout = window.setTimeout(function(){
                                    tooltip.hide();
                                }, 500);
                            });


                            tooltip.getEl().on('mouseleave', function(){
                                if (timeout) {
                                    timeout = window.setTimeout(function(){
                                        tooltip.hide();
                                    }, 500);
                                }
                            });

                            tooltip.getEl().on('mouseenter', function(){
                                window.clearTimeout(timeout);
                            });


                        });

                        // Show the tooltip only if there is something to show,
                        // and offset by width of layertree panel
                        if (abstractText) {
                            this.tooltip.showAt([treemanager.dom.offsetWidth, e.xy[1]]);
                            //Resize height when content changes
                            if (this.tooltip.getHeight() > this.tooltip.boxMaxHeight) {
                                this.tooltip.autoHeight = false;
                                this.tooltip.setHeight(this.tooltip.boxMaxHeight);
                            } else {
                                this.tooltip.autoHeight = true;
                            }
                        }


                    }
                }
                this.tree.fireEvent('mouseover', this.tree.getNodeById(nodeId), e);

            }
        }
    }
});

Ext.preg(gxp.plugins.LayerTree.prototype.ptype, gxp.plugins.LayerTree);

/**
 * Handle moving of records in layertree data store
 */
Ext.data.Store.prototype.move = function(record, to){
    //var r = this.getAt(from);
    this.data.remove(record);
    this.data.insert(to, record);
    this.fireEvent("load", this, to);
};

