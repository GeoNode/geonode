Ext.namespace("GeoExplorer");

GeoExplorer.GroupContainer = Ext.extend(GeoExt.tree.LayerContainer, {

    /** api: config[group]
     *  ``String``
     *  Only layer records with a group field value that matches this value
     *  will be added to the container.  If not provided, then only layer
     *  records with null or undefined group field value will be added to the
     *  container.
     */
    
    /**
     * Constructor: GeoExplorer.GroupContainer
     * 
     * Parameters:
     * config - {Object}
     */
    constructor: function(config) {
        config.text = config.text || "Layers";
        this.group = config.group;
        GeoExplorer.GroupContainer.superclass.constructor.apply(this, arguments);
        this.on({
            insert: this.onChildAdd,
            append: this.onChildAdd,
            scope: this
        });
    },

    /** private: method[render]
     *  :param bulkRender: ``Boolean``
     */
    render: function(bulkRender) {
        var first = !this.rendered;
        GeoExplorer.GroupContainer.superclass.render.call(this, bulkRender);
        if (first) {
            this.layerStore.on({
                update: this.onStoreUpdate,
                scope: this
            });
        }
    },
    
    /** private: method[onStoreAdd]
     *  :param store: ``Ext.data.Store``
     *  :param records: ``Array(Ext.data.Record)``
     *  :param index: ``Number``
     *  
     *  Listener for the store's add event.
     */
    onStoreAdd: function(store, records, index) {
        /**
         * Containers with checkedGroup should have only one visible layer.
         * This listener can be removed if the LayerNode is made to fire
         * checkchange when the radio button is unchecked.
         * TODO: http://www.geoext.org/trac/geoext/ticket/109
         */
        GeoExplorer.GroupContainer.superclass.onStoreAdd.apply(this, arguments);
        if (this.defaults && this.defaults.checkedGroup && !this._reordering) {
            Ext.each(records, function(record) {
                this.enforceOneVisible(record);
            }, this);
        }
    },

    /** private: method[onStoreRemove]
     *  :param store: ``Ext.data.Store``
     *  :param record: ``Ext.data.Record``
     *  :param index: ``Number``
     *  
     *  Listener for the store's remove event.
     */
    onStoreRemove: function(store, record, index) {
        /**
         * Containers with checkedGroup should have only one visible layer.
         * This listener can be removed if the LayerNode is made to fire
         * checkchange when the radio button is unchecked.
         * TODO: http://www.geoext.org/trac/geoext/ticket/109
         */
        GeoExplorer.GroupContainer.superclass.onStoreRemove.apply(this, arguments);
        if (this.defaults && this.defaults.checkedGroup && !this._reordering) {
            var layer = this.lastChild && this.lastChild.layer;
            if (layer) {
                var last;
                this.layerStore.each(function(rec) {
                    if (rec.get("layer") === layer) {
                        last = rec;
                    }
                    return !last;
                });
                if (last) {
                    this.enforceOneVisible(last);
                }
            }
        }
    },


    /** private: onStoreUpdate
     *  :param store: ``Ext.data.Store``
     *  :param record: ``Ext.data.Record``
     *  :param operation: ``String``
     *  
     *  Listener for the store's update event.
     */
    onStoreUpdate: function(store, record, operation) {
        /**
         * Containers with checkedGroup should have only one visible layer.
         * This listener can be removed if the LayerNode is made to fire
         * checkchange when the radio button is unchecked.
         * TODO: http://www.geoext.org/trac/geoext/ticket/109
         */
        if (this.defaults && this.defaults.checkedGroup) {
            this.enforceOneVisible(record);
        }
    },
    
    /** private: enforceOneVisible
     *  TODO: remove this when http://www.geoext.org/trac/geoext/ticket/109 is closed
     */
    enforceOneVisible: function(record) {
        var layer = record.get("layer");
        var inGroup = false;
        this.eachChild(function(node) {
            if(node.layer === layer) {
                inGroup = true;
            }
            return !inGroup;
        });
        if(inGroup) {
            var vis = layer.getVisibility();
            if(vis) {
                // make sure there is not more than one
                this.eachChild(function(node) {
                    if(node.layer !== layer && node.layer.getVisibility()) {
                        window.setTimeout(function() {
                            node.layer.setVisibility(false);
                        }, 0);
                    }
                });
            } else {
                // make sure there is at least one
                this.eachChild(function(node) {
                    vis = vis || node.layer.getVisibility();
                });
                if(!vis) {
                    window.setTimeout(function() {
                        record.get("layer").setVisibility(true);
                    }, 0);
                }
            }
        }
    },

    /** private: method[addLayerNode]
     *  :param layerRecord: ``Ext.data.Record`` The layer record containing the
     *      layer to be added.
     *  :param index: ``Number`` Optional index for the new layer.  Default is 0.
     *  
     *  Adds a child node representing a layer of the map
     */
    addLayerNode: function(layerRecord, index) {
        if (layerRecord.get("group") == this.group) {
            GeoExplorer.GroupContainer.superclass.addLayerNode.apply(
                this, arguments
            );
        }
    },
    
    /** private: method[removeLayerNode]
     *  :param layerRecord: ``Ext.data.Record`` The layer record containing the
     *      layer to be removed.
     * 
     *  Removes a child node representing a layer of the map
     */
    removeLayerNode: function(layerRecord) {
        if (layerRecord.get("group") == this.group) {
            GeoExplorer.GroupContainer.superclass.removeLayerNode.apply(
                this, arguments
            );
    	}
    },

    /** private: method[recordIndexToNodeIndex]
     *  :param index: ``Number`` The record index in the layer store.
     *  :return: ``Number`` The appropriate child node index for the record.
     */
    recordIndexToNodeIndex: function(index) {
        var store = this.layerStore;
        var count = store.getCount();
        var nodeCount = this.childNodes.length;
        var nodeIndex = -1;
        var record;
        for(var i=count-1; i>=0; --i) {
            record = store.getAt(i);
            if(record.get("layer").displayInLayerSwitcher &&
               record.get("group") == this.group) {
                ++nodeIndex;
                if(index === i || nodeIndex > nodeCount-1) {
                    break;
                }
            }
        };
        return nodeIndex;
    },

    /** private: method[nodeIndexToRecordIndex]
     *  :param index: ``Number`` The child node index.
     *  :return: ``Number`` The appropriate record index for the node.
     *  
     *  Convert a child node index to a record index.
     */
    nodeIndexToRecordIndex: function(index) {
        var store = this.layerStore;
        var count = store.getCount();
        var nodeIndex = -1;
        var layer = this.item(index).layer;
        var record;
        for(var i=count-1; i>=0; --i) {
            record = store.getAt(i);
            if(layer.displayInLayerSwitcher &&
               (record.get("group") == this.group)) {
                ++nodeIndex;
                if(index === nodeIndex) {
                    break;
                }
            }
        }
        return i;
    },

    /** private: method[onChildMove]
     *  :param tree: ``Ext.data.Tree``
     *  :param node: ``Ext.tree.TreeNode``
     *  :param oldParent: ``Ext.tree.TreeNode``
     *  :param newParent: ``Ext.tree.TreeNode``
     *  :param index: ``Number``
     *  
     *  Listener for child node "move" events.  This updates the order of
     *  records in the store based on new node order if the node has not
     *  changed parents.
     */
    onChildAdd: function(tree, container, node) {
        var record = this.layerStore.getAt(
            this.layerStore.findBy(function(record) {
                return record.get("layer") === node.layer;
            })
        );
        if(record.get("group") !== this.group) {
            window.setTimeout(function() {
                var store = container.layerStore;
                var index = container.indexOf(node);
                store.remove(record);
                node.remove();
                
                // TODO: record.clone()
                Ext.data.Record.AUTO_ID++;
                record = record.copy(Ext.data.Record.AUTO_ID);    
                var layer = record.get("layer").clone();
                record.set("layer", null);
                record.set("layer", layer);

                record.set("group", container.group);

                // TODO: if this is the only record of this group, recIndex is not determined
                // this is a hack that works for two groups only
                if (container.childNodes.length == 0) {
                    if (tree.root.firstChild === container) {
                        store.add([record]);
                    } else {
                        store.insert(0, [record]);
                    }
                } else {
                    var sib = container.childNodes[index];
                    var offset = 1;
                    if (!sib) {
                        offset = 0;
                        sib = container.lastChild;
                    }
                    var recIndex = store.findBy(function(rec) {
                        return (rec.get("layer") === sib.layer);
                    }) + offset;
                    store.insert(recIndex, [record]);
                }
            }, 0);
            
        }
    },

    /** private: method[destroy]
     */
    destroy: function() {
        if(this.layerStore) {
            this.layerStore.un("update", this.onStoreUpdate, this);
        }
        GeoExplorer.GroupContainer.superclass.destroy.apply(this, arguments);
    }


});
