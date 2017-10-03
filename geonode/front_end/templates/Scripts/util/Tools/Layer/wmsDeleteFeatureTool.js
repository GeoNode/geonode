mapModule.factory('WmsDeleteFeatureTool', [
    'featureService', 'jantrik.Event',
    function (featureService, Event) {
        return function WmsDeleteFeatureTool(surfLayer, wmsSelectFeatureTool) {
            var isActivated = false;
            var _thisTool = this;
            
            this.events = new Event();

            this.deleteFeature = function(surfFeature, flags) {
                featureService.deleteFeature(surfFeature).success(function() {
                    surfLayer.refresh();
                    _thisTool.events.broadcast('deleted', surfFeature, flags);
                });
            };

            this.activate = function () {
                if (!isActivated) {
                    wmsSelectFeatureTool.activate();
                    isActivated = true;
                }
            };

            this.deactivate = function () {
                if (isActivated) {
                    deactivate();
                }
            };

            function deactivate() {
                wmsSelectFeatureTool.deactivate();
                isActivated = false;
            }

            this.dispose = function(disponeComponents) {
                if (disponeComponents) {
                    wmsSelectFeatureTool.dispose(disponeComponents);
                }
            };

            wmsSelectFeatureTool.events.register('selected', _thisTool.deleteFeature);

            deactivate();
        };
    }
]);