appModule.factory('ClearFeaturesTool', ['layerService',
    function (layerService) {
        return function ClearFeaturesTool(surfLayer) {
            var _thisTool = this;

            _thisTool.clear = function() {
                return layerService.clearFeatures(surfLayer);
            };

            _thisTool.dispose = function() {
            }
        }
    }
]);
