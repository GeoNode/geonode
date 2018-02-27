mapModule.factory('WmsSelectFeatureTool', [
    'featureService', 'jantrik.Event', 'surfFeatureFactory',
    function (featureService, Event, surfFeatureFactory) {
        function WmsSelectFeature(olMap, surfLayer, olLayer, surfMap, options) {
            var isActivated = false;
            
            var _lastSuccessfulUrl;
            options = options || {};
            var _thisTool = this;
            var currentEvent = undefined;

            this.events = new Event();

            this.selectedFeatures = [];

            this.unselectAllFeatures = function () {
                _thisTool.selectedFeatures.length = 0;
                featureService.setActive(null);
                _thisTool.events.broadcast('allUnSelected');
            };

            function setSelected(surfFeature, olFeature) {
                if (!options.multiple) {
                    _thisTool.unselectAllFeatures(true);
                }

                _thisTool.selectedFeatures.push(surfFeature);

                if (_thisTool.selectedFeatures.length === 1) {
                    featureService.setActive(surfFeature);
                } else {
                    featureService.setActive(null);
                }

                _thisTool.events.broadcast('selected', surfFeature, olFeature);
            };

            this.activate = function () {
                if (!isActivated) {
                    olMap.on('singleclick', getFeature);
                    isActivated = true;
                    _thisTool.events.broadcast('selectToolActivated');
                }
            };

            this.deactivate = function () {
                if (isActivated) {
                    deactivate();
                    _thisTool.events.broadcast('selectToolDeactivated');
                }
            };

            function deactivate() {
                olMap.un('singleclick', getFeature);
                isActivated = false;
            }

            this.dispose = function () {
                _thisTool.deactivate();
            };

            this.getCurrentEvent = function () {
                return currentEvent;
            };

            this.featureReceived = function (feature) {
                if (feature) {
                    setSelected(feature.surfFeature, feature.olFeature);
                    surfMap.updateSelectionLayer([feature.olFeature.id_]);
                } else {
                    _thisTool.unselectAllFeatures();
                    surfMap.updateSelectionLayer(null);
                }
            }
            function featureReceived (feature) {
                if (feature) {
                    setSelected(feature.surfFeature, feature.olFeature);
                    surfMap.updateSelectionLayer([feature.olFeature.id_]);
                } else {
                    _thisTool.unselectAllFeatures();
                    surfMap.updateSelectionLayer(null);
                }
            }
            function getFeature(event) {
                currentEvent = event;
                if (surfLayer.IsVisible) {
                    var wmsSource = olLayer.getSource();
                    var view = olMap.getView();
                    var viewResolution = view.getResolution();
                    var viewProjection = view.getProjection();
                    var url = wmsSource.getGetFeatureInfoUrl(
                        event.coordinate, viewResolution, viewProjection,
                        { 'INFO_FORMAT': 'application/vnd.ogc.gml', 'FEATURE_COUNT': '1' });

                    _lastSuccessfulUrl = null;
                    surfFeatureFactory.getFeatureFromUrl(url, surfLayer).then(function(features) {
                        _lastSuccessfulUrl = url;

                        featureReceived(features[0]);
                    }).catch(function() {
                        featureReceived(null);
                    });
                }
            }
            
            this.reloadCurrentFeature = function() {
                if (_lastSuccessfulUrl && _thisTool.selectedFeatures.length) {
                    surfFeatureFactory.getFeatureFromUrl(_lastSuccessfulUrl);
                }
            };

            deactivate();
        }

        return WmsSelectFeature;
    }
]);