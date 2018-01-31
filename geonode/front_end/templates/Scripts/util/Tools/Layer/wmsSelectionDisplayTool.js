mapModule.factory('WmsSelectionDisplayTool', [
    'jantrik.Event',
    function (Event) {

        return function WmsSelectionDisplayTool(surfLayer, selectFeatureTool,interactiveLayer) {
            var isActivated = false;
            var _thisTool = this;
            var _olInteractiveSource = interactiveLayer.getSource();

            this.events = new Event();

            function setStyle() {
                // var selectedStyle = surfLayer.getSelectedOlStyle() || {};

                //interactiveLayer.setStyle(selectedStyle);
            }

            function unselectAllFeatures() {
                selectFeatureTool.unselectAllFeatures();
            }

            this.activate = function () {
                if (!isActivated) {
                    selectFeatureTool.activate();
                    setStyle();
                    isActivated = true;
                }
            };

            this.unselectAllFeatures = unselectAllFeatures;

            this.deactivate = function () {
                if (isActivated) {
                    deactivate();
                }
            };

            function deactivate() {
                selectFeatureTool.unselectAllFeatures();
                selectFeatureTool.deactivate();
                isActivated = false;
            }

            this.dispose = function (disposeComponents) {
                if (disposeComponents) {
                    selectFeatureTool.dispose(disposeComponents);
                }
            };

            this.innerTool = selectFeatureTool;

            selectFeatureTool.events.register('selected', function (surfFeature, olFeature) {
                if (!surfLayer.IsVisible) return;

                //_olInteractiveSource.clear();
                //_olInteractiveSource.addFeature(olFeature);

                //_thisTool.events.broadcast('selected', surfFeature, olFeature);
            }).register('allUnSelected', function () {
                //_olInteractiveSource.clear({ fast: true });

                _thisTool.events.broadcast('allUnSelected');
            });

            surfLayer.events.register('styleChanged', setStyle).register('refreshed', unselectAllFeatures);

            deactivate();
        };
    }
]);
