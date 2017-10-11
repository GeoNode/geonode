mapModule.factory('mapService', [
    'mapRepository', 'SurfMap', 'layerService', 'layerStyleGenerator', 'mapTools',
    function(mapRepository, SurfMap, layerService, layerStyleGenerator, mapTools) {
        var map;

        var factory = {
            setSurfMap: function(surfMap) {
                map = surfMap;
                factory.events = map.events;
                factory.getZoom = map.getZoom;
                factory.zoomToLevel = map.zoomToLevel;
                factory.sortableLayers = map.sortableLayers;
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
            addDataLayer: function(dataId, dataType, shapeType) {
                var data;
                if (dataType === "raster") {
                    data = {
                        dataId: dataId,
                        style: layerStyleGenerator.generateDefaultRasterStyle()
                    }
                    data.sldStyle = layerStyleGenerator.getSldStyle(shapeType, data.style.default,
                        true, null);
                    data.selectionStyleSld = layerStyleGenerator.getSldStyle(shapeType, data.style.select,
                        true, null);

                    busyStateManager.showBusyState(appMessages.busyState.addLayer);
                    mapRepository.createRasterDataLayer(data).success(function(layerInfo) {
                        map.addLayer(layerInfo);
                    }).finally(function() {
                        busyStateManager.hideBusyState();
                    });
                } else {
                    data = {
                        dataId: dataId,
                        style: layerStyleGenerator.generate(shapeType)
                    }

                    data.sldStyle = layerStyleGenerator.getSldStyle(shapeType, data.style.default,
                        true, null);
                    data.selectionStyleSld = layerStyleGenerator.getSldStyle(shapeType, data.style.select,
                        true, null);

                    busyStateManager.showBusyState(appMessages.busyState.addLayer);
                    mapRepository.createDataLayer(data).success(function(layerInfo) {
                        map.addLayer(layerInfo);
                    }).finally(function() {
                        busyStateManager.hideBusyState();
                    });
                }
            },
            addDataLayer: function(layer) {
                var mapInfo = { "MapId": "s_1b8c9bb9583e4c5dba1f1fa322db52e7_wm", "Name": "test1", "OwnerId": "s_1b8c9bb9583e4c5dba1f1fa322db52e7", "LastUpdateOn": "2017-01-16T00:00:00Z", "IsLocked": false, "IsDraft": true, "SavedMapId": "s_8bf2cfa9088547b08635ee189cced8f7", "IsPublic": false, "PublicId": "s_8dd26ece0118475e8af50b2487f78c2f", "BaseLayerName": "", "Title": null, "Description": null, "IsAuthorNamePublic": false, "IsDirty": true, "Layers": [{ "LayerId": "s_8a01c4261c0e40b1b50787f45e650a47", "Name": "Pipe", "SortOrder": 1, "LastUpdateOn": "2017-10-10T11:10:07.136Z", "ClassifierDefinitions": {}, "CanWrite": true, "DataId": "s_4c07628ba25e4eb78b741cc8421932ce", "ShapeType": "polyline", "Style": { "Name": "s_2a5bd0a9688342868783c23eec61053e", "default": { "fillPattern": null, "textFillColor": null, "text": null, "pixelDensity": null, "strokeDashstyle": "solid", "strokeWidth": 1.0, "strokeColor": "#FF0010", "strokeOpacity": null, "fillOpacity": null, "fillColor": null, "pointRadius": null, "graphicName": null, "textGraphicName": null, "externalGraphic": null }, "select": { "fillPattern": "", "textFillColor": "#222026", "text": null, "pixelDensity": null, "strokeDashstyle": "solid", "strokeWidth": 1.0, "strokeColor": "#0000ff", "strokeOpacity": 1.0, "fillOpacity": 0.4, "fillColor": "#0000ff", "pointRadius": 6.0, "graphicName": "circle", "textGraphicName": null, "externalGraphic": null }, "labelConfig": { "attribute": null, "visibilityZoomLevel": 0, "font": "Times", "fontStyle": "normal", "fontWeight": "normal", "color": "#000000", "borderColor": "#ffffff", "showBorder": true, "size": 10.0, "alignment": 1.0, "offsetX": 0.0, "offsetY": 0.0, "rotation": 0.0, "followLine": false, "repeat": false, "repeatInterval": 5.0, "wrap": false, "wrapPixel": 50.0 } }, "VisualizationSettings": null, "IsVisible": true, "Filters": [], "ZoomLevel": 0, "ModificationState": "Unchanged", "LayerExtent": { "MinX": 10063404.3716531, "MinY": 2728268.617362, "MaxX": 10064319.7161516, "MaxY": 2729175.79233018 }, "AttributeDefinition": [{ "Id": "s_43d6a020abcb4526b03b534bc5a69d8e", "Name": "material", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 25, "Precision": null, "Scale": null }, { "Id": "s_4ae976a337f84e09b0b157130b0ade20", "Name": "length_m", "AttributeName": null, "IsPublished": true, "Type": "number", "Length": null, "Precision": 19, "Scale": 11 }, { "Id": "s_837c10e73c1e4ccbaa9c18aa1cd67c48", "Name": "zone_id", "AttributeName": null, "IsPublished": true, "Type": "number", "Length": null, "Precision": 19, "Scale": 11 }, { "Id": "s_39da768593134163995b5dd9b51f8ed6", "Name": "location", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 50, "Precision": null, "Scale": null }, { "Id": "s_93b9d15b96d342e3a0c0a57b64040a13", "Name": "thana", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 50, "Precision": null, "Scale": null }, { "Id": "s_d4cfb982cfc84e90879dccc625a4b512", "Name": "contractor", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 75, "Precision": null, "Scale": null }, { "Id": "s_4c3522e8c3244d2ca44de8da09f98039", "Name": "digitizer", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 75, "Precision": null, "Scale": null }, { "Id": "s_b697a7dee74e4212a9e83ebaaea7d0b6", "Name": "startnode", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 50, "Precision": null, "Scale": null }, { "Id": "s_70bfbcbb5f3d45e7aa35ee486cb78351", "Name": "endnode", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 50, "Precision": null, "Scale": null }, { "Id": "s_68aa3c095f6e4116905a4d5d418e835b", "Name": "inst_date", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 50, "Precision": null, "Scale": null }, { "Id": "s_46995e65e0f64277a0445de384f0fbc5", "Name": "roadname", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 50, "Precision": null, "Scale": null }, { "Id": "s_42eb0a25402b44f78e1dc690f06961e8", "Name": "nom_dia", "AttributeName": null, "IsPublished": true, "Type": "number", "Length": null, "Precision": 4, "Scale": 0 }, { "Id": "s_1926a41719df46ffb97adef2daf7d54a", "Name": "pipe_type", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 50, "Precision": null, "Scale": null }, { "Id": "s_08495ed8f2114cb5a3dc78c1aab8dd54", "Name": "authority", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 50, "Precision": null, "Scale": null }, { "Id": "s_9f4821bdadfa49d4a36543544da1f0a7", "Name": "lastupdate", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 50, "Precision": null, "Scale": null }, { "Id": "s_ef0ce900ccb44fb79544e5f0b15f2649", "Name": "status", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 50, "Precision": null, "Scale": null }, { "Id": "s_e8671d74be734414be07c7ec3d48d6fc", "Name": "comments", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 100, "Precision": null, "Scale": null }, { "Id": "s_cceea120771a4692866abb84850a15bd", "Name": "project", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 50, "Precision": null, "Scale": null }, { "Id": "s_733b431187f54b5abe51470cac589bf9", "Name": "pipeid", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 50, "Precision": null, "Scale": null }], "IdColumn": "gid", "LinearUnit": "metre", "IsLocked": false, "DataSourceName": "Pipe", "SourceFileExists": true, "IsDataOwner": true, "IsRaster": false, "SavedDataId": "s_301563ba5aac421fac15badf3494ece9" }, { "LayerId": "s_31b086d815f5492a9da932bbf9af7333", "Name": "illinois_poi", "SortOrder": 2, "LastUpdateOn": "2017-10-10T11:10:26.083Z", "ClassifierDefinitions": {}, "CanWrite": true, "DataId": "s_facf34ee54914605943fe987f5b3637c", "ShapeType": "point", "Style": { "Name": "s_a5170c56d2a64a0c8ee7dff53d916e71", "default": { "fillPattern": null, "textFillColor": "#222026", "text": null, "pixelDensity": null, "strokeDashstyle": "solid", "strokeWidth": 1.0, "strokeColor": "#5EF1F2", "strokeOpacity": null, "fillOpacity": 0.75, "fillColor": "#2f7979", "pointRadius": 14.0, "graphicName": "circle", "textGraphicName": null, "externalGraphic": null }, "select": { "fillPattern": "", "textFillColor": "#222026", "text": null, "pixelDensity": null, "strokeDashstyle": "solid", "strokeWidth": 1.0, "strokeColor": "#0000ff", "strokeOpacity": 1.0, "fillOpacity": 0.4, "fillColor": "#0000ff", "pointRadius": 6.0, "graphicName": "circle", "textGraphicName": null, "externalGraphic": null }, "labelConfig": { "attribute": null, "visibilityZoomLevel": 0, "font": "Times", "fontStyle": "normal", "fontWeight": "normal", "color": "#000000", "borderColor": "#ffffff", "showBorder": true, "size": 10.0, "alignment": 1.0, "offsetX": 0.0, "offsetY": 0.0, "rotation": 0.0, "followLine": false, "repeat": false, "repeatInterval": 5.0, "wrap": false, "wrapPixel": 50.0 } }, "VisualizationSettings": null, "IsVisible": true, "Filters": [], "ZoomLevel": 0, "ModificationState": "Added", "LayerExtent": { "MinX": -9818543.41779904, "MinY": 5183814.6260749, "MaxX": -9770487.95134629, "MaxY": 5235883.07751104 }, "AttributeDefinition": [{ "Id": "s_985cd4386b6a4762812371ca8ae4c5a3", "Name": "category", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 30, "Precision": null, "Scale": null }, { "Id": "s_5d1416d309df49cab55858ff2b463f70", "Name": "name", "AttributeName": null, "IsPublished": true, "Type": "text", "Length": 92, "Precision": null, "Scale": null }], "IdColumn": "gid", "LinearUnit": "Meter", "IsLocked": false, "DataSourceName": "illinois_poi", "SourceFileExists": true, "IsDataOwner": true, "IsRaster": false, "SavedDataId": "s_fe297a3305394811919f33cdb16fc30d" }], "PropertyInPopup": true, "InitialExtent": { "XMin": 0.0, "YMin": 0.0, "XMax": 0.0, "YMax": 0.0 } };

                var newLayer = mapInfo.Layers[1];
                newLayer.Name = layer.Name;
                newLayer.LayerExtent = {
                    "MinX": layer.BoundingBox[0]._minx,
                    "MinY": layer.BoundingBox[0]._miny,
                    "MaxX": layer.BoundingBox[0]._maxx,
                    "MaxY": layer.BoundingBox[0]._maxy
                };
                map.addLayer(newLayer, false);
                factory.updateLayerViewOrders();
            },
            removeLayer: function(layerId) {
                map.removeLayer(layerId);
                mapRepository.removeLayer(layerId);
            },
            saveMapAs: function(name) {
                map.Name = name;
                busyStateManager.showBusyState(appMessages.busyState.save);

                return mapRepository.saveAs(name).success(function() {
                    busyStateManager.hideBusyState();
                }).error(function() {
                    busyStateManager.hideBusyState();
                });
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
                return map;
            }

        };

        return factory;
    }
]);