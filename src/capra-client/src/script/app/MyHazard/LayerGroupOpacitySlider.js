Ext.namespace("MyHazard");

MyHazard.LayerGroupOpacitySlider = Ext.extend(GeoExt.LayerOpacitySlider, {
    layers: null,

    changeLayerOpacity: function(slider, value) {
        for (var i = 0, len = this.layers.length; i < len; i++) {
            GeoExt.LayerOpacitySlider.prototype.changeLayerOpacity.apply(
                {layer: this.layers[i]}, [slider, value]
            );
        }
    },

    changeLayerVisibility: function(slider, value) {
        // Mask the default functionality; we want to maintain the visibility 
        // flag even when opacity is set to 0
    }
});

