mapModule.factory('mapService', [
    'mapRepository', 'SurfMap', 'layerService', 'layerStyleGenerator', 'mapTools', 'LayerService', '$q',
    function(mapRepository, SurfMap, layerService, layerStyleGenerator, mapTools, newLayerService, $q) {
        var map;

        function _mapSource(source) {
            return angular.extend({
                "url": "",
                "restUrl": "/gs/rest",
                "title": "Local Geoserver",
                "projection": "EPSG:4326",
                "id": "3",
                "baseParams": {
                    "SERVICE": "WMS",
                    "REQUEST": "GetCapabilities",
                    "TILED": true,
                    "VERSION": "1.1.1"
                }
            }, source);
        }

        function _mapLayers(layer) {
            return {
                "source": layer.source,
                "name": layer.Name,
                "title": layer.Name,
                "visibility": layer.IsVisible,
                "opacity": 1,
                "group": "background",
                "fixed": true,
                "selected": false,
                "type": "OpenLayers.Layer",
                "args": [
                    "No background"
                ]
            };
        }

        function _map(name, abstract, organizationId, categoryId) {
            var sources = [];
            var layers = map.layers;
            var mapped_layers = [];
            var mapped_sources = {};
            i = 0;
            for (var k in layers) {
                var e = layers[k];
                var url = e.olLayer.getSource().getUrls()[0];
                var index = sources.indexOf(url);
                if (index == -1) {
                    sources.push(url);
                    e.source = i.toString();
                    mapped_sources[e.source] = _mapSource({ url: url });
                } else {
                    e.source = index.toString();
                }
                mapped_layers.push(_mapLayers(e));
                i++;
            };

            return {
                "map": {
                    "layers": mapped_layers,
                    "center": map.getView().getCenter(),
                    "units": map.getProjection().getUnits(),
                    "maxResolution": map.getView().getResolution(),
                    "maxExtent": map.getProjection().getExtent(),
                    "zoom": map.getZoom(),
                    "projection": map.getProjection().getCode()
                },
                "about": {
                    "abstract": abstract,
                    "title": name,
                    "organization": organizationId,
                    "category": categoryId
                },
                "sources": angular.extend({
                    "search": {
                        "ptype": "gxp_geonodeapicataloguesource",
                        "restUrl": "/gs/rest",
                        "url": "/api/layers/",
                        "projection": "EPSG:4326",
                        "id": "search"
                    }
                }, mapped_sources)
            };
        }

        var factory = {
            setSurfMap: function(surfMap) {
                map = surfMap;
                factory.addInteraction = surfMap.addInteraction;
                factory.removeInteraction = map.removeInteraction;
                factory.events = map.events;
                factory.getZoom = map.getZoom;
                factory.zoomToLevel = map.zoomToLevel;
                factory.sortableLayers = map.sortableLayers;
                factory.zoomToExtent = map.zoomToExtent;
                factory.getInteractions = map.getInteractions;
                factory.removeUserInteractions = map.removeUserInteractions;
                factory.registerEvent = map.registerEvent;
                factory.removeEvents = map.removeEvents;
                factory.addVectorLayer = map.addVectorLayer;
                factory.getProjection = map.getProjection;
                factory.removeVectorLayer = map.removeVectorLayer;
            },
            loadMap: function(mapInfo) {
                mapTools.baseMap.setBaseMapByName(mapInfo.BaseLayerName);
                map.openMap(mapInfo);
                var surfLayers = map.sortableLayers;
                for (var i in surfLayers) {
                    factory.updateLayerViewOrders();
                }
            },
            loadWorkingMap: function() {
                var mapInfo = {
                    // "MapId": "s_c7a3f3a632a0477ca090ae876d5b56e9",
                    // "Name": "rgtrgvr",
                    // "OwnerId": "s_c0f7878481c546a8b3cc27479a516b32",
                    // "LastUpdateOn": "2017-01-10T06:01:26.451Z",
                    // "IsLocked": false,
                    "IsDraft": true,
                    // "SavedMapId": "s_9f7029846ea7428a914f85348cf7eda5",
                    // "IsPublic": false,
                    // "PublicId": "s_18c0563060544068bcd058d2bb7655bd",
                    // "BaseLayerName": "Google Street",
                    // "Title": null,
                    // "Description": null,
                    // "IsAuthorNamePublic": false,
                    // "IsDirty": true,
                    // "Layers": [{
                    //     "LayerId": "s_950085eadbd246b5bbea00407c7066d0",
                    //     "Name": "test1",
                    //     "SortOrder": 1,
                    //     "LastUpdateOn": "2017-09-28T11:14:09.068Z",
                    //     "ClassifierDefinitions": {},
                    //     "CanWrite": true,
                    //     "DataId": "s_3a0134358eb84b84967e3d61d7221900",
                    //     "ShapeType": "point",
                    //     "Style": {
                    //         "Name": "s_e4e9502ac60d42ba82adfe9ac5bcf95d",
                    //         "default": {
                    //             "fillPattern": null,
                    //             "textFillColor": "#222026",
                    //             "text": null,
                    //             "pixelDensity": null,
                    //             "strokeDashstyle": "solid",
                    //             "strokeWidth": 1.0,
                    //             "strokeColor": "#FFCC99",
                    //             "strokeOpacity": null,
                    //             "fillOpacity": 0.75,
                    //             "fillColor": "#80664c",
                    //             "pointRadius": 14.0,
                    //             "graphicName": "circle",
                    //             "textGraphicName": null,
                    //             "externalGraphic": null
                    //         },
                    //         "select": {
                    //             "fillPattern": "",
                    //             "textFillColor": "#222026",
                    //             "text": null,
                    //             "pixelDensity": null,
                    //             "strokeDashstyle": "solid",
                    //             "strokeWidth": 1.0,
                    //             "strokeColor": "#0000ff",
                    //             "strokeOpacity": 1.0,
                    //             "fillOpacity": 0.4,
                    //             "fillColor": "#0000ff",
                    //             "pointRadius": 6.0,
                    //             "graphicName": "circle",
                    //             "textGraphicName": null,
                    //             "externalGraphic": null
                    //         },
                    //         "labelConfig": {
                    //             "attribute": null,
                    //             "visibilityZoomLevel": 0,
                    //             "font": "Times",
                    //             "fontStyle": "normal",
                    //             "fontWeight": "normal",
                    //             "color": "#000000",
                    //             "borderColor": "#ffffff",
                    //             "showBorder": true,
                    //             "size": 10.0,
                    //             "alignment": 1.0,
                    //             "offsetX": 0.0,
                    //             "offsetY": 0.0,
                    //             "rotation": 0.0,
                    //             "followLine": false,
                    //             "repeat": false,
                    //             "repeatInterval": 5.0,
                    //             "wrap": false,
                    //             "wrapPixel": 50.0
                    //         }
                    //     },
                    //     "VisualizationSettings": null,
                    //     "IsVisible": true,
                    //     "Filters": [],
                    //     "ZoomLevel": 0,
                    //     "ModificationState": "Unchanged",
                    //     "LayerExtent": {
                    //         "MinX": -2543824.30133067,
                    //         "MinY": 3522218.26338092,
                    //         "MaxX": 5733388.6176145,
                    //         "MaxY": 5439870.42899942
                    //     },
                    //     "AttributeDefinition": [],
                    //     "IdColumn": "gid",
                    //     "LinearUnit": "metre",
                    //     "IsLocked": false,
                    //     "DataSourceName": "test1",
                    //     "SourceFileExists": true,
                    //     "IsDataOwner": true,
                    //     "IsRaster": false,
                    //     "SavedDataId": "s_843fee180d644202beac1699ae89dc25"
                    // }],
                    // "PropertyInPopup": true,
                    // "InitialExtent": {
                    //     "XMin": 0.0,
                    //     "YMin": 0.0,
                    //     "XMax": 0.0,
                    //     "YMax": 0.0
                    // }
                };
                layerService.fetchLayers().then(function(layers) {
                        mapInfo.Layers = layers;
                        factory.loadMap(mapInfo);
                    })
                    // return mapRepository.getWorkingMapInfo().success(function (mapInfo) {
                    //     factory.loadMap(mapInfo);
                    // });
            },
            getMapExtent: function() {
                return map.getExtent();
            },
            loadPublicMap: function(publicId) {
                mapRepository.getMapInfo(publicId).success(function(mapInfo) {
                    factory.loadMap(mapInfo);
                });
            },
            openWorkingMap: function(mapId) {
                busyStateManager.showBusyState(appMessages.busyState.openMap);

                mapRepository.openMap(mapId).success(function() {

                    factory.loadWorkingMap().finally(function() {
                        busyStateManager.hideBusyState();
                    });

                }).error(function() {
                    busyStateManager.hideBusyState();
                });
            },
            getCategoryList: function() {
                return mapRepository.getCategoryList();
            },
            closeWorkingMap: function() {
                map.closeMap();
                mapRepository.closeMap();
            },
            saveBaseLayerName: function(baseLayerName) {
                if (map.BaseLayerName != baseLayerName) {
                    map.BaseLayerName = baseLayerName;
                    mapRepository.saveBaseLayerName(baseLayerName);
                }
            },
            addBlankLayer: function(name, featureType) {
                var data = {
                    name: name,
                    shapeType: featureType,
                    style: layerStyleGenerator.generate(featureType)
                }
                data.sldStyle = layerStyleGenerator.getSldStyle(featureType, data.style.default,
                    true, null);
                data.selectionStyleSld = layerStyleGenerator.getSldStyle(featureType, data.style.select,
                    true, null);

                busyStateManager.showBusyState(appMessages.busyState.addLayer);
                mapRepository.createBlankLayer(data).success(function(layerInfo) {
                    map.addLayer(layerInfo, true);
                }).finally(function() {
                    busyStateManager.hideBusyState();
                });
            },
            // addDataLayer: function(dataId, dataType, shapeType) {
            //     var data;
            //     if (dataType === "raster") {
            //         data = {
            //             dataId: dataId,
            //             style: layerStyleGenerator.generateDefaultRasterStyle()
            //         }
            //         data.sldStyle = layerStyleGenerator.getSldStyle(shapeType, data.style.default,
            //             true, null);
            //         data.selectionStyleSld = layerStyleGenerator.getSldStyle(shapeType, data.style.select,
            //             true, null);

            //         busyStateManager.showBusyState(appMessages.busyState.addLayer);
            //         mapRepository.createRasterDataLayer(data).success(function(layerInfo) {
            //             map.addLayer(layerInfo);
            //         }).finally(function() {
            //             busyStateManager.hideBusyState();
            //         });
            //     } else {
            //         data = {
            //             dataId: dataId,
            //             style: layerStyleGenerator.generate(shapeType)
            //         }

            //         data.sldStyle = layerStyleGenerator.getSldStyle(shapeType, data.style.default,
            //             true, null);
            //         data.selectionStyleSld = layerStyleGenerator.getSldStyle(shapeType, data.style.select,
            //             true, null);

            //         busyStateManager.showBusyState(appMessages.busyState.addLayer);
            //         mapRepository.createDataLayer(data).success(function(layerInfo) {
            //             map.addLayer(layerInfo);
            //         }).finally(function() {
            //             busyStateManager.hideBusyState();
            //         });
            //     }
            // },
            addDataLayer: function(layer, override) {
                var p1_deferred = $q.defer()
                var p1 = p1_deferred.promise;
                mapId = this.getId();
                if (!mapId) {
                    p1 = newLayerService.getStyleByLayer(layer.Name)
                        .then(function(res) {
                            layer.Style = res;
                        }, function() {
                            layer.Style = newLayerService.getNewStyle();
                        });
                } else {
                    newLayerService.getLayerByMap(mapId, layer.Name)
                        .then(function(res) {
                            newLayerService.getStyle(res.styles)
                                .then(function(res) {
                                    layer.Style = res;
                                    layer.ClassifierDefinitions = layer.Style.classifierDefinitions || {};
                                    p1_deferred.resolve({});
                                }, function() {
                                    layer.Style = newLayerService.getNewStyle();
                                    layer.ClassifierDefinitions = layer.Style.classifierDefinitions || {};
                                    p1_deferred.resolve({});
                                });
                        }, function() {
                            layer.Style = newLayerService.getNewStyle();
                            layer.ClassifierDefinitions = new_layer.Style.classifierDefinitions || {};
                            p1_deferred.resolve({});
                        });
                }
                var p2 = newLayerService.getAttributesName(layer.Name)
                    .then(function(res) {
                        layer.AttributeDefinition = res;
                    });
                var p3 = newLayerService.getShapeType(layer.Name)
                    .then(function(res) {
                        layer.ShapeType = res;
                    });

                $q.all([p1, p2, p3])
                    .then(function() {
                        map.addLayer(layer, true);
                    });
            },
            removeLayer: function(layerId) {
                map.removeLayer(layerId);
                mapRepository.removeLayer(layerId);
            },
            saveMapAs: function(name, abstract, organizationId, categoryId) {
                var mapObj = _map(name, abstract, organizationId, categoryId);
                mapObj.id = factory.getId();
                busyStateManager.showBusyState(appMessages.busyState.save);
                if (!mapObj.id) {
                    return mapRepository.saveAs(mapObj).success(function(res) {
                        busyStateManager.hideBusyState();
                        saveSuccess(res.id, name, abstract);
                    }).error(function() {
                        busyStateManager.hideBusyState();
                    });
                } else {
                    return mapRepository.update(mapObj).success(function() {
                        busyStateManager.hideBusyState();
                        saveSuccess(mapObj.id, name, abstract);

                    }).error(function() {
                        busyStateManager.hideBusyState();
                    });
                }

                function saveSuccess(id, name, abstract) {
                    factory.setId(id);
                    factory.setMapName(name);
                    factory.setMeta({ abstract: abstract });

                    for (var k in map.layers) {
                        var layer = map.layers[k];
                        var style = layer.getStyle();
                        factory.updateMapLayer(id, layer.Name, {
                            styles: style.id
                        });
                    }
                }
            },
            updateMapLayer: function(mapId, layerName, obj) {
                return mapRepository.updateMapLayer(mapId, layerName, obj);
            },
            getLayers: function() {
                return map.getLayers();
            },
            getLayer: function(layerId) {
                return map.getLayer(layerId);
            },
            setFeatureSelected: function(fid, isSelected) {
                map.setFeatureSelected(fid, isSelected);
            },
            setAllFeaturesUnselected: function() {
                //map.setAllFeaturesUnselected();
            },
            updateSize: function() {
                map.updateSize();
            },
            isEmbedded: function() {
                return map.isEmbedded;
            },
            setMapName: function(name) {
                map.Name = name;
            },
            getMapName: function() {
                return map.Name;
            },
            getMapInfo: function() {
                return map.info;
            },
            isEmpty: function() {
                return map.isEmpty();
            },
            updateLayerViewOrders: function() {
                map.updateLayerViewOrders();
            },
            showPropertyInPopup: function() {
                return map.info && map.info.PropertyInPopup;
            },
            getMap: function() {
                return map.getMap();
            },
            getId: function() {
                return map.Id;
            },
            setId: function(id) {
                map.Id = id;
            },
            setMeta: function(meta) {
                map.Meta = meta;
            },
            getMeta: function() {
                return map.Meta || {};
            }

        };

        return factory;
    }
]);