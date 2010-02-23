/** api: (define)
 *  module = GeoExplorer
 *  class = Embed
 *  base_link = GeoExplorer
 */

/** api: constructor
 *  ..class:: GeoExplorer.Embed(config)
 *
 *  Create a GeoExplorer that knows how to preview a single layer with switchable styles etc.
 */
LayerPreview = Ext.extend(Embed, {
    setPreviewStyle: function(stylename) {
        function isPreviewedLayer(rec) {
            var index = this.layerSources.find("identifier", rec.get("source_id"))
            return index != -1; // the previewed layer is the only one that is not a background layer
        }

        var layerIndex = this.layers.findBy(isPreviewedLayer, this);
        if (layerIndex != -1) {
            this.layers.getAt(layerIndex).get("layer").mergeNewParams({"styles": stylename});
        }
    },

    createTools: function() {
        var backgroundTree = new GeoExt.tree.BaseLayerContainer({
            text: this.backgroundContainerText, 
            layerStore: this.layers, 
            loader: {
                filter: function(record) {
                    return record.get('group') === 'background';
                }
            }
        });

        return [{
            text: this.backgroundContainerText, 
            menu: new Ext.menu.Menu({
                items: [new Ext.tree.TreePanel({
                    border: false,
                    rootVisible: false,
                    loader: { applyLoader: false },
                    root: backgroundTree
                })]
            })
        }];
    }
});
