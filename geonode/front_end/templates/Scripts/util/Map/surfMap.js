mapModule.factory('SurfMap', ['surfLayerFactory', 'featureService', 'jantrik.Event', 'ol', '$rootScope',
    function(surfLayerFactory, featureService, Event, ol, $rootScope) {
        return function SurfMap(olMap) {
            var _userInteractions = [];
            var _userEvents = [];
            var factory = this;
            factory.autoCenterToCurrentLocation = true;
            factory.events = new Event();
            factory.addInteraction = function(interaction) {
                _userInteractions.push(interaction);
                olMap.addInteraction(interaction);
            };
            factory.removeUserInteractions = function() {
                _userInteractions.forEach(function(interaction) {
                    factory.removeInteraction(interaction);
                }, this);
            };

            factory.registerEvent = function(type, cb) {
                var id = olMap.on(type, cb);
                _userEvents.push(id);
            };
            factory.removeEvents = function() {
                _userEvents.forEach(function(element) {
                    olMap.unByKey(element);
                }, this);
            };
            factory.getInteractions = function() {
                return olMap.getInteractions();
            }
            factory.removeInteraction = function(interaction) {
                olMap.removeInteraction(interaction);
            }
            factory.addVectorLayer = function(layer){
                olMap.addLayer(layer);
            };
            factory.openMap = function(mapInfo) {

                angular.extend(factory, mapInfo);
                factory.info = mapInfo;

                factory.events.broadcast('infoLoaded', mapInfo);

                for (var j in mapInfo.Layers) {
                    var layerInfo = mapInfo.Layers[j];
                    factory.addLayer(layerInfo, true);
                }
                factory.addSelectionLayer();

                if (mapInfo.IsDraft) {
                    factory.zoomToMap();
                } else {
                    factory.zoomToExtent([mapInfo.InitialExtent.XMin, mapInfo.InitialExtent.YMin,
                        mapInfo.InitialExtent.XMax, mapInfo.InitialExtent.YMax
                    ]);
                }
                
            };
            

            var _layers = {};
            var _dataIdLayerMapper = {};

            factory.updateSelectionLayer = function(fids) {
                if (!_selectionLayer) return;
                if (fids) {
                    var dataIds = [],
                        selectionStyles = [];

                    for (var i in fids) {
                        var dataId = fids[i].split('.')[0];
                        dataIds.push(dataId);
                        selectionStyles.push(_dataIdLayerMapper[dataId].getSelectStyleName());
                    }

                    _selectionLayer.getSource().updateParams({
                        LAYERS: dataIds.join(','),
                        STYLES: selectionStyles.join(','),
                        featureid: fids.join(',')
                    });
                } else {
                    _selectionLayer.getSource().updateParams({
                        LAYERS: '',
                        STYLES: '',
                        featureid: '?'
                    });
                }
            }

            factory.closeMap = function() {
                factory.Name = null;
                for (var id in _layers) {
                    factory.removeLayer(id, true);
                }
                factory.updateSelectionLayer(null);
                featureService.setActive(null);
                factory.events.broadcast('closed');
            };

            factory.isEmpty = function() {
                return Object.keys(_layers).length == 0;
            };

            factory.layers = _layers;

            factory.getLayers = function() {
                return _layers;
            };

            var NullLayer = surfLayerFactory.createSurfLayer();

            function getLayer(layerId) {
                return _layers[layerId] || NullLayer;
            }
            factory.getLayer = getLayer;

            var _selectionLayer;

            factory.addSelectionLayer = function() {
                _selectionLayer = surfLayerFactory.createSelectionLayer();
                olMap.topLayers.getLayers().push(_selectionLayer);
            };

            $rootScope.$on('refreshSelectionLayer', function() {
                refreshSelectionLayer();
            });

            function refreshSelectionLayer() {
                _selectionLayer.getSource().updateParams({ time_: (new Date()).getTime() });
            }

            factory.addLayer = function(layerInfo, preventZoom) {
                var surfLayer = surfLayerFactory.createSurfLayer(layerInfo);
                var layerId = surfLayer.getId();
                _layers[layerId] = surfLayer;
                _dataIdLayerMapper[surfLayer.getDataId()] = surfLayer;
                factory.sortableLayers.push(surfLayer);
                surfLayer.setMap(olMap);
                factory.events.broadcast('layerAdded', surfLayer);

                if (!preventZoom) {
                    factory.zoomToExtent(surfLayer.getMapExtent());
                }

                return surfLayer;
            };

            factory.removeLayer = function(layerId, closing) {
                var surfLayer = getLayer(layerId);
                surfLayer.markRemoved();

                delete _layers[layerId];
                removeLayerFromSortableLayers(layerId);

                surfLayerFactory.disposeSurfLayer(surfLayer);

                factory.events.broadcast('layerRemoved', surfLayer, closing);
            };

            factory.sortableLayers = [];

            function removeLayerFromSortableLayers(layerId) {
                var s = 0;
                for (s in factory.sortableLayers) {
                    if (factory.sortableLayers[s].getId() == layerId) {
                        break;
                    }
                }
                factory.sortableLayers.splice(s, 1);
            }

            // TODO: move this to a TOOL
            factory.updateLayerViewOrders = function() {
                var midLayers = olMap.midLayers.getLayers();
                midLayers.clear();

                var totalLayers = factory.sortableLayers.length;
                for (var i = totalLayers - 1; i >= 0; i--) {
                    var surfLayer = factory.sortableLayers[i];
                    surfLayer.SourceFileExists && midLayers.push(surfLayer.olLayer);
                }
            };

            factory.getZoom = function() {
                return olMap.getView().getZoom();
            };

            factory.getExtent = function() {
                return olMap.getView().calculateExtent(olMap.getSize());
            }
            factory.getProjection = function(){
                return olMap.getView().getProjection();
            }

            factory.zoomToLevel = function(zoomLevel) {
                olMap.getView().setZoom(zoomLevel);
            };

            factory.zoomToExtent = function(extent) {
                var empty = ol.extent.isEmpty(extent);
                empty = empty || extent.every(function(val) {
                    return val == 0;
                });

                if (!empty) {
                    olMap.getView().fit(extent, olMap.getSize());
                }
            };
            factory.removeVectorLayer = function(vectorLayer){
                olMap.removeLayer(vectorLayer);
            };

            factory.zoomToMap = function() {
                var _extent;
                if (!Object.keys(_layers)) {
                    _extent = ol.extent.boundingExtent([-7840475.2212513, 3033355.8490402, 7911667.5655651, 5361933.4783957]);
                } else {
                    _extent = ol.extent.createEmpty();
                    angular.forEach(_layers, function(layer) {
                        _extent = ol.extent.extend(_extent, layer.getMapExtent());
                    });
                }

                factory.zoomToExtent(_extent);
            };

            factory.updateSize = function() {
                olMap.updateSize();
            };

            factory.getMap = function(){
                return olMap;
            };
        };
    }
]);