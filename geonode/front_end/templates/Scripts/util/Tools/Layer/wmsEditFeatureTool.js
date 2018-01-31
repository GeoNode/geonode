mapModule.factory('WmsEditFeatureTool', [
    'featureService', 'jantrik.Event', 'surfFeatureFactory',
    function (featureService, Event, surfFeatureFactory) {
        return function WmsEditFeatureTool(surfLayer, wmsSelectFeatureTool, olModifyInteraction, olInteractiveSource, featureCollection) {
            var isActivated = false;
            var _thisTool = this;
            var _oldSurfFeature;
            var _olModifyingFeature;
            var _modified = false;

            this.isEditing = false;

            this.events = new Event();

            this.editFeature = function (newSurfFeature, oldSurfFeature, flags) {
                return featureService.editFeature(newSurfFeature).success(function () {
                    surfLayer.refresh();

                    _thisTool.events.broadcast('edited', newSurfFeature, oldSurfFeature, flags);
                });
            };

            this.activate = function () {
                if (!isActivated) {
                    wmsSelectFeatureTool.activate();
                    olModifyInteraction.setActive(true);
                    isActivated = true;
                }
            };

            this.deactivate = function () {
                if (isActivated) {
                    deactivate();
                }
            };

            function deactivate() {
                _thisTool.saveModification();
                wmsSelectFeatureTool.deactivate();
                olModifyInteraction.setActive(false);
                isActivated = false;
            }

            function bindModifiedEvent(feature) {
                feature && feature.on('change', function () {
                    _modified = true;
                });
            }

            this.dispose = function (olMap, disposeComponents) {
                if (disposeComponents) {
                    wmsSelectFeatureTool.dispose(disposeComponents);
                }
                olMap.removeInteraction(olModifyInteraction);
            };

            function removeModifyingFeature() {
                if (_olModifyingFeature) {
                    olInteractiveSource.removeFeature(_olModifyingFeature);
                    featureCollection.remove(_olModifyingFeature);
                    _olModifyingFeature = null;
                }
                _modified = false;
            }

            this.saveModification = function () {
                if (_modified) {
                    var newSurfFeature = surfFeatureFactory.createSurfFeature(_olModifyingFeature, surfLayer);
                    _thisTool.editFeature(newSurfFeature, _oldSurfFeature);
                }

                removeModifyingFeature();
                _thisTool.isEditing = false;
                _modified = false;
            }

            wmsSelectFeatureTool.events.register('selected', function (surfFeature, olFeature) {
                removeModifyingFeature();

                surfFeatureFactory.getCompleteFeature(surfFeature).then(function (completeOlFeature) {
                    _olModifyingFeature = completeOlFeature;
                    bindModifiedEvent(_olModifyingFeature);

                    olInteractiveSource.addFeature(_olModifyingFeature);
                    featureCollection.push(_olModifyingFeature);

                    _thisTool.isEditing = true;
                    _oldSurfFeature = surfFeature.clone();
                });
            }).register('allUnSelected', function () {
                _thisTool.saveModification();
            });

            if (surfLayer.getFeatureType() === 'point') {
                olModifyInteraction.on('modifyend', function () {
                    _thisTool.saveModification();
                });
            }

            

            deactivate();
        };
    }
]);