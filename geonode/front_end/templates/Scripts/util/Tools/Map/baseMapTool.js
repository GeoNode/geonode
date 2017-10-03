mapModule.factory('BaseMapTool', [
    'ol', 'google', 'jantrik.Event', 'reprojection',
    function (ol, google, Event, reprojection) {

        function BaseMapTool(olMap, googleMap) {
            var _thisTool = this;
            this.events = new Event();

            var _olMapView = olMap.getView();
            var _gmapDiv = googleMap.getDiv();

            _gmapDiv._originalOpacity = _gmapDiv.style.opacity;
            _gmapDiv.style.opacity = 0;

            var _currentBaseMap = {};

            this.setBaseMapByName = function (baseMapName) {
                var baseMap = _.findWhere(_allBaseMaps, { title: baseMapName }) || _allBaseMaps[0];
                if (baseMap.isGoogle) {
                    _gmapDiv.style.opacity = _gmapDiv._originalOpacity;
                    googleMap.setMapTypeId(baseMap.mapTypeId);
                } else {
                    baseMap.olLayer.setVisible(true);
                }
                _currentBaseMap = baseMap;

                _thisTool.events.broadcast('set');
            };

            this.changeBaseLayer = function (newBaseMap) {
                if (_currentBaseMap != newBaseMap) {
                    if (newBaseMap.isGoogle) {
                        if (!_currentBaseMap.isGoogle) {
                            _currentBaseMap.olLayer.setVisible(false);
                            _gmapDiv.style.opacity = _gmapDiv._originalOpacity;
                        }
                        googleMap.setMapTypeId(newBaseMap.mapTypeId);
                    } else {
                        if (_currentBaseMap.isGoogle) {
                            _gmapDiv.style.opacity = 0;
                        } else {
                            _currentBaseMap.olLayer.setVisible(false);
                        }
                        newBaseMap.olLayer.setVisible(true);
                    }

                    _thisTool.events.broadcast('changed', newBaseMap.title, _currentBaseMap.title);
                    _currentBaseMap = newBaseMap;
                }
            };

            this.getBaseMap = function () {
                return _currentBaseMap;
            };

            this.getAllBaseMaps = function () {
                return _allBaseMaps;
            };

            var _gBaseMaps = getGBaseMaps();
            var _olBaseMaps = getOlBaseMaps();
            var _allBaseMaps = _gBaseMaps.concat(_olBaseMaps);

            _olBaseMaps.forEach(function (olBaseMap) {
                olMap.bottomLayers.getLayers().push(olBaseMap.olLayer);
            });

            _olMapView.on('change:center', synchCenter);
            _olMapView.on('change:resolution', synchZoom);
            olMap.on('change:size', function () {
                setTimeout(function () {
                    google.maps.event.trigger(googleMap, "resize");
                    synchZoom();
                    synchCenter();
                }, 1);
            });

            function synchCenter() {
                var center = reprojection.coordinate.toLatLong(_olMapView.getCenter());
                googleMap.setCenter(new google.maps.LatLng(center[1], center[0]));
            }

            function synchZoom() {
                googleMap.setZoom(_olMapView.getZoom());
            }
        }

        function getGBaseMaps() {
            return [
                {
                    title: 'Google Street',
                    isGoogle: true,
                    mapTypeId: google.maps.MapTypeId.ROADMAP
                }, {
                    title: 'Google Terrain',
                    isGoogle: true,
                    mapTypeId: google.maps.MapTypeId.TERRAIN
                }, {
                    title: 'Google Hybrid',
                    isGoogle: true,
                    mapTypeId: google.maps.MapTypeId.HYBRID
                }, {
                    title: 'Google Satellite',
                    isGoogle: true,
                    mapTypeId: google.maps.MapTypeId.SATELLITE
                }
            ];
        }

        function getOlBaseMaps() {
            return [
                {
                    title: 'Open Street Map',
                    olLayer: new ol.layer.Tile({
                        title: 'Open Street Map',
                        visible: false,
                        source: new ol.source.OSM()
                    })
                }, {
                    title: 'Map Quest Satellite',
                    olLayer: new ol.layer.Tile({
                        title: 'Map Quest Satellite',
                        visible: false,
                        source: new ol.source.MapQuest({ layer: 'sat' })
                    })
                }, {
                    title: 'No Map',
                    olLayer: new ol.layer.Image({
                        title: 'No Map',
                        type: 'base',
                        visible: false,
                        extent: reprojection.extent.to3857([-180, -90, 180, 90]),
                        source: new ol.source.ImageStatic({
                            url: './Content/assets/images/empty.jpg',
                            imageExtent: reprojection.extent.to3857([-180, -90, 180, 90]),
                            imageSize: [128, 128],
                            attributions: [
                                new ol.Attribution({
                                    html: '&nbsp'
                                })
                            ]
                        })
                    })
                }
            ];
        }

        return BaseMapTool;
    }
]);