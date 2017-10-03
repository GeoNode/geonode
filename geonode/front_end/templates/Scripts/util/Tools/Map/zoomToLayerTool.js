mapModule.factory('ZoomToLayerTool', [
    function () {
        return function ZoomToLayerTool(surfMap) {
            this.zoom = function(surfLayer) {
                if (!surfLayer.isEmpty()) {
                    surfMap.zoomToExtent(surfLayer.getMapExtent());
                }
            };
        };
    }
]);