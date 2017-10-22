mapModule.factory('mapToolsFactory', [
    'ol',
    'GeoLocationTool',
    'LocationSearchTool',
    'ActiveLayerTool',
    'ZoomToLayerTool',
    'ZoomTrackerTool',
    'BaseMapTool',
    'AllSelectableLayerTool',
    'NavigationHistoryTool',
    'WmsMultiSelectFeatureTool',
    'ZoomInOutTool',
    function (ol, GeoLocationTool, LocationSearchTool, ActiveLayerTool, ZoomToLayerTool, ZoomTrackerTool, BaseMapTool, AllSelectableLayerTool, NavigationHistoryTool, WmsMultiSelectFeatureTool, ZoomInOutTool) {
        var _markerSource;
        var _olMap, _olView;
        var _gMap;
        var _surfMap;

        function initialize(surfMap, olMap, gMap) {
            _surfMap = surfMap;
            _olMap = olMap;
            _olView = _olMap.getView();
            _gMap = gMap;
        }

        function getMarkerOverlay() {
            if (!_markerSource) {

                _markerSource = new ol.source.Vector({
                    features: new ol.Collection(),
                    useSpatialIndex: false,
                    updateWhileAnimating: true,
                    updateWhileInteracting: true
                });

                _olMap.topLayers.getLayers().push(new ol.layer.Vector({
                    source: _markerSource
                }));

            }

            return _markerSource;
        }

        function createGeoLocationTool() {
            var _locationMarker = new ol.Feature();
            var _accuracyFeature = new ol.Feature();

            _locationMarker.setStyle(new ol.style.Style({
                image: new ol.style.Circle({
                    radius: 6,
                    fill: new ol.style.Fill({
                        color: '#3399CC'
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#FFF',
                        width: 2
                    })
                })
            }));

            getMarkerOverlay().addFeature(_locationMarker);
            getMarkerOverlay().addFeature(_accuracyFeature);

            var olGeolocation = new ol.Geolocation({
                projection: _olMap.getView().getProjection(),
                trackingOptions: {
                    enableHighAccuracy: false,
                    maximumAge: 600000,
                    timeout: 10000
                }
            });

            return new GeoLocationTool(_locationMarker, _accuracyFeature, _olView, olGeolocation);
        };

        function createLocationSearchTool() {
            var _searchMarker = new ol.Feature();
            _searchMarker.setStyle(
                new ol.style.Style({
                    image: new ol.style.Icon({
                        anchor: [0.5, 1],
                        src: '/static/Content/assets/images/marker.png'
                    })
                }));

            getMarkerOverlay().addFeature(_searchMarker);

            return new LocationSearchTool(_searchMarker, _olMap);
        }

        function createActiveLayerTool(interactionHandler) {
            return new ActiveLayerTool(_surfMap, interactionHandler);
        }

        function createZoomToLayerTool() {
            return new ZoomToLayerTool(_surfMap, _olMap);
        }

        function createZoomTrackerTool() {
            return new ZoomTrackerTool(_olMap);
        }

        function createBaseMapTool() {
            return new BaseMapTool(_olMap, _gMap);
        }

        function createAllSelectableLayerTool() {
            return new AllSelectableLayerTool(_surfMap);
        }

        function createNavigationHistoryTool() {
            return new NavigationHistoryTool(_olMap);
        }

        function createSelectFeatureTool() {
            return new WmsMultiSelectFeatureTool(_olMap, _surfMap);
        }

        function createZoomInOutTool() {
            return new ZoomInOutTool(_olView);
        }

        return {
            initialize: initialize,
            createGeoLocationTool: createGeoLocationTool,
            createLocationSearchTool: createLocationSearchTool,
            createActiveLayerTool: createActiveLayerTool,
            createZoomToLayerTool: createZoomToLayerTool,
            createZoomTrackerTool: createZoomTrackerTool,
            createBaseMapTool: createBaseMapTool,
            createAllSelectableLayerTool: createAllSelectableLayerTool,
            createNavigationHistoryTool: createNavigationHistoryTool,
            createSelectFeatureTool: createSelectFeatureTool,
            createZoomInOutTool: createZoomInOutTool
        };
    }
]);