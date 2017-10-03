mapModule.factory('CreateFeatureTool', [
    'surfFeatureFactory', 'jantrik.Event', 'featureService', 'ol',
    function (surfFeatureFactory, Event, featureService, ol) {
        return function (surfLayer, olDrawInteraction, olInteractiveSource) {
            var isActivated = false;
            var _thisTool = this;
            this.events = new Event();

            _thisTool.isCreating = false;

            this.activate = function () {
                if (!isActivated) {
                    olDrawInteraction.setActive(true);
                    isActivated = true;
                }
            };

            this.deactivate = function () {
                if (isActivated) {
                    deactivate();
                }
            };

            function deactivate() {
                olDrawInteraction.setActive(false);
                isActivated = false;
            }

            this.dispose = function (olMap) {
                olDrawInteraction.setActive(false);
                olMap.removeInteraction(olDrawInteraction);
            };

            this.createFeature = function (surfFeature, flags) {
                return featureService.createFeature(surfFeature, flags && (flags.undo || flags.redo)).then(function () {
                    surfLayer.addFeature(surfFeature);

                    surfLayer.refresh();
                    _thisTool.events.broadcast('created', surfFeature, flags);
                });
            };

            this.createGeometry = function (olGeometry) {
                var olFeature = new ol.Feature({
                    geometry: olGeometry
                });
                olInteractiveSource.addFeature(olFeature);
                addOlFeature(olFeature);
            };

            this.saveCreation = function () {
                if (_thisTool.isCreating) {
                    if (surfLayer.ShapeType != 'point') {
                        olDrawInteraction.getActive() && olDrawInteraction.finishDrawing();
                    }
                }
            };

            function addOlFeature(olFeature) {
                _thisTool.isCreating = false;
                var surfFeature = surfFeatureFactory.createSurfFeature(olFeature, surfLayer);
                _thisTool.createFeature(surfFeature).then(function () {
                    olInteractiveSource.removeFeature(olFeature);
                });
            }

            olDrawInteraction.on('drawend', function (event) {
                addOlFeature(event.feature);
            });

            olDrawInteraction.on('drawstart', function () {
                _thisTool.isCreating = true;
            });

            deactivate();
        };
    }
]);