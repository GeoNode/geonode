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
                //var _allBaseMaps = getOlBaseMaps();
    
    
    
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
    
                        mapTypeId: google.maps.MapTypeId.ROADMAP,
                        groupName: 'Google'
    
                    }, {
    
                        title: 'Google Terrain',
    
                        isGoogle: true,
    
                        mapTypeId: google.maps.MapTypeId.TERRAIN,
                        groupName: 'Google'
    
                    }, {
    
                        title: 'Google Hybrid',
    
                        isGoogle: true,
    
                        mapTypeId: google.maps.MapTypeId.HYBRID,
                        groupName: 'Google'
    
                    }, {
    
                        title: 'Google Satellite',
    
                        isGoogle: true,
    
                        mapTypeId: google.maps.MapTypeId.SATELLITE,
                        groupName: 'Google'
    
                    }
    
                ];
    
            }
    
            function addxyzPart(baseMaps, groupName, xyzPart){
                _.each(baseMaps, function(item){
                    item.url = item.url + xyzPart;
                    item.groupName = groupName;
                });
            }
    
            function getThunderForestBaseMaps(){
                var thunderForestAPIKey = '50d64afdbe424011bdaabb6b9315b7ed';
                var baseMaps = [];
                var urlRoot = 'http://tile.thunderforest.com/';
                baseMaps.push({title: 'Thuderforest(OpenCycleMap)', url: urlRoot+'cycle/'});
                baseMaps.push({title: 'Thuderforest(Transport)', url: urlRoot+'transport/'});
                baseMaps.push({title: 'Thuderforest(TransportDark)', url: urlRoot+'transport-dark/'});
                baseMaps.push({title: 'Thuderforest(SpinalMap)', url: urlRoot+'spinal-map/'});
                baseMaps.push({title: 'Thuderforest(Landscape)', url: urlRoot+'landscape/'});
                baseMaps.push({title: 'Thuderforest(Outdoors)', url: urlRoot+'outdoors/'});
                baseMaps.push({title: 'Thuderforest(Pioneer)', url: urlRoot+'pioneer/'});
                addxyzPart(baseMaps, 'Thunderforest', '{z}/{x}/{y}.png?apikey=' + thunderForestAPIKey);
                return baseMaps;
            }
    
            function getStamenBaseMaps(){
                var baseMaps = [];
                var urlRoot = 'https://stamen-tiles.a.ssl.fastly.net/';
                baseMaps.push({title: 'Stamen.Toner', url: urlRoot+'toner/'});
                baseMaps.push({title: 'Stamen.TonerLite', url: urlRoot+'toner-lite/'});
                baseMaps.push({title: 'Stamen.Watercolor', url: urlRoot+'watercolor/'});
                baseMaps.push({title: 'Stamen.Terrain', url: urlRoot+'terrain/'});
                baseMaps.push({title: 'Stamen.TerrainBackground', url: urlRoot+'terrain-background/'});
                addxyzPart(baseMaps, 'Stamen', '{z}/{x}/{y}.png');
                return baseMaps;
            }
    
            function getEsriBaseMaps(){
                var baseMaps = [];
                var urlRoot = 'https://server.arcgisonline.com/ArcGIS/rest/services/';
                baseMaps.push({title: 'Esri.WorldStreetMap', url: urlRoot+'World_Street_Map/MapServer/tile/'});
                baseMaps.push({title: 'Esri.DeLorme', url: urlRoot+'Specialty/DeLorme_World_Base_Map/MapServer/tile/'});
                baseMaps.push({title: 'Esri.WorldTopoMap', url: urlRoot+'World_Topo_Map/MapServer/tile/'});
                baseMaps.push({title: 'Esri.WorldImagery', url: urlRoot+'World_Imagery/MapServer/tile/'});
                baseMaps.push({title: 'Esri.WorldShadedRelief', url: urlRoot+'World_Shaded_Relief/MapServer/tile/'});
                baseMaps.push({title: 'Esri.OceanBasemap', url: urlRoot+'Ocean_Basemap/MapServer/tile/'});
                baseMaps.push({title: 'Esri.NatGeoWorldMap', url: urlRoot+'NatGeo_World_Map/MapServer/tile/'});
                addxyzPart(baseMaps, 'ESRI', '{z}/{y}/{x}');
                return baseMaps;
            }
    
            function getOSMBaseMaps(){
                var baseMaps = [];
                var urlRoot = 'https://tile.openstreetmap.org/';
                baseMaps.push({title: 'Open Street Map', url: 'https://tile.openstreetmap.org/'});
                baseMaps.push({title: 'Open Street Map (Black and White)', url: 'http://tiles.wmflabs.org/bw-mapnik/'});
                baseMaps.push({title: 'Open Street Map (HOT)', url: 'http://tile.openstreetmap.fr/hot/'});
                baseMaps.push({title: 'Open Topo Map', url: urlRoot+'http://tile.opentopomap.org/'});
                // https://aerial.maps.cit.api.here.com/maptile/2.1/maptile/newest/hybrid.day/{z}/{x}/{y}/{size}/{format}?app_id={app_id}&app_code={app_code}&lg=eng
    
                addxyzPart(baseMaps, 'OpenStreetMap', '{z}/{x}/{y}.png');
                return baseMaps;
            }
    
            function getOlBaseMaps() {
    
                var baseLayers = [
    
                    {
    
                        title: 'Map Quest Satellite',
    
                        olLayer: new ol.layer.Tile({
    
                            title: 'Map Quest Satellite',
    
                            visible: false,
    
                            source: new ol.source.MapQuest({ layer: 'sat' })
    
                        }),
                        groupName: 'Others'
    
                    }, {
    
                        title: 'No Map',
    
                        olLayer: new ol.layer.Image({
    
                            title: 'No Map',
    
                            type: 'base',
    
                            visible: false,
    
                            extent: reprojection.extent.to3857([-180, -90, 180, 90]),
    
                            source: new ol.source.ImageStatic({
    
                                url: '/static/Content/assets/images/empty.jpg',
    
                                imageExtent: reprojection.extent.to3857([-180, -90, 180, 90]),
    
                                imageSize: [128, 128],
    
                                attributions: [
    
                                    new ol.Attribution({
    
                                        html: '&nbsp'
    
                                    })
    
                                ]
    
                            })
    
                        }),
                        groupName: 'Others'
    
                    }
    
                ];
    
                // var allBaseMaps = {
                //     'OSM': getOSMBaseMaps(),
                //     'ThunderForest': getThunderForestBaseMaps(),
                //     'Stamen': getStamenBaseMaps(),
                //     'ESRI': getEsriBaseMaps()
                // };
                var otherBaseLayers = [];
    
                otherBaseLayers = otherBaseLayers.concat(getOSMBaseMaps(),
                    getThunderForestBaseMaps(), 
                    getStamenBaseMaps(),
                    getEsriBaseMaps());
    
                var olLayers = _.map(otherBaseLayers, function(item){
    
                    return {
    
                        title: item.title,
    
                        olLayer: new ol.layer.Tile({
    
                            title: item.title,
    
                            visible: false,
    
                            source: new ol.source.XYZ({
    
                                url: item.url
    
                              })
    
                        }),
                        groupName: item.groupName
    
                    };
    
                });
    
                return olLayers.concat(baseLayers);
                //return allBaseMaps;
    
            }
    
    
    
            return BaseMapTool;
    
        }
    
    ]);