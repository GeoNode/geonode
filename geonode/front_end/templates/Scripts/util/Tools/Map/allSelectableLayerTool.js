mapModule.factory('AllSelectableLayerTool', [
    function() {
        return function AllSelectableLayerTool(surfMap) {
            surfMap.events.register('layerAdded', function(surfLayer) {
                surfLayer.tools.selectFeature.activate();
            }).register('layerRemoved', function (surfLayer) {
                surfLayer.tools.selectFeature.deactivate();
            });
        };
    }
]);