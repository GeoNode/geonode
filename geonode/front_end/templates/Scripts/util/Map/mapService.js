mapModule.factory('mapService', [
    'mapRepository', 'SurfMap', 'layerService', 'layerStyleGenerator', 'mapTools',
    function(mapRepository, SurfMap, layerService, layerStyleGenerator, mapTools) {
        var map;

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

                var newLayer = {
                    "LayerId": "s_31b086d815f5492a9da932bbf9af7333",
                    "Name": "illinois_poi",
                    "SortOrder": 2,
                    "LastUpdateOn": "2017-10-10T11:10:26.083Z",
                    "ClassifierDefinitions": {},
                    "CanWrite": true,
                    // "DataId": "s_facf34ee54914605943fe987f5b3637c",
                    "ShapeType": "point",
                    "Style": {
                        "Name": "s_a5170c56d2a64a0c8ee7dff53d916e71",
                        "default": {
                            "fillPattern": null,
                            "textFillColor": "#222026",
                            "text": null,
                            "pixelDensity": null,
                            "strokeDashstyle": "solid",
                            "strokeWidth": 1.0,
                            "strokeColor": "#5EF1F2",
                            "strokeOpacity": null,
                            "fillOpacity": 0.75,
                            "fillColor": "#2f7979",
                            "pointRadius": 14.0,
                            "graphicName": "circle",
                            "textGraphicName": null,
                            "externalGraphic": null
                        },
                        "select": {
                            "fillPattern": "",
                            "textFillColor": "#222026",
                            "text": null,
                            "pixelDensity": null,
                            "strokeDashstyle": "solid",
                            "strokeWidth": 1.0,
                            "strokeColor": "#0000ff",
                            "strokeOpacity": 1.0,
                            "fillOpacity": 0.4,
                            "fillColor": "#0000ff",
                            "pointRadius": 6.0,
                            "graphicName": "circle",
                            "textGraphicName": null,
                            "externalGraphic": null
                        },
                        "labelConfig": {
                            "attribute": null,
                            "visibilityZoomLevel": 0,
                            "font": "Times",
                            "fontStyle": "normal",
                            "fontWeight": "normal",
                            "color": "#000000",
                            "borderColor": "#ffffff",
                            "showBorder": true,
                            "size": 10.0,
                            "alignment": 1.0,
                            "offsetX": 0.0,
                            "offsetY": 0.0,
                            "rotation": 0.0,
                            "followLine": false,
                            "repeat": false,
                            "repeatInterval": 5.0,
                            "wrap": false,
                            "wrapPixel": 50.0
                        }
                    },
                    "VisualizationSettings": null,
                    "IsVisible": true,
                    "Filters": [],
                    "ZoomLevel": 0,
                    "ModificationState": "Added",
                    "LayerExtent": {
                        "MinX": -9818543.41779904,
                        "MinY": 5183814.6260749,
                        "MaxX": -9770487.95134629,
                        "MaxY": 5235883.07751104
                    },
                    "AttributeDefinition": [{
                        "Id": "s_985cd4386b6a4762812371ca8ae4c5a3",
                        "Name": "category",
                        "AttributeName": null,
                        "IsPublished": true,
                        "Type": "text",
                        "Length": 30,
                        "Precision": null,
                        "Scale": null
                    }, {
                        "Id": "s_5d1416d309df49cab55858ff2b463f70",
                        "Name": "name",
                        "AttributeName": null,
                        "IsPublished": true,
                        "Type": "text",
                        "Length": 92,
                        "Precision": null,
                        "Scale": null
                    }],
                    "IdColumn": "gid",
                    "LinearUnit": "Meter",
                    "IsLocked": false,
                    "DataSourceName": "illinois_poi",
                    "SourceFileExists": true,
                    "IsDataOwner": true,
                    "IsRaster": false,
                    "SavedDataId": "s_fe297a3305394811919f33cdb16fc30d"
                };
                newLayer.Name = layer.Name;
                newLayer.LayerExtent = {
                    "MinX": layer.BoundingBox[0]._minx,
                    "MinY": layer.BoundingBox[0]._miny,
                    "MaxX": layer.BoundingBox[0]._maxx,
                    "MaxY": layer.BoundingBox[0]._maxy
                };
                newLayer.geoserverUrl = layer.geoserverUrl;
                map.addLayer(newLayer, true);
                // factory.updateLayerViewOrders();
            },
            removeLayer: function(layerId) {
                map.removeLayer(layerId);
                mapRepository.removeLayer(layerId);
            },
            saveMapAs: function(name) {
                var mapObj = {
                    // "proxy": "/proxy/?url=",
                    // "printService": "http://demo.geonode.org/geoserver/pdf/",
                    // "rest": "/maps/",
                    // "ajaxLoginUrl": "/account/ajax_login",
                    // "homeUrl": "/",
                    // "localGeoServerBaseUrl": "http://demo.geonode.org/geoserver/",
                    // "localCSWBaseUrl": "http://demo.geonode.org/catalogue/csw",
                    "csrfToken": "L3gCVHu8cQmPtwEm44xUuYk7Rx1NOn0i",
                    // "listeners": {},
                    // "defaultSourceType": "gxp_wmscsource",
                    "about": {
                        "abstract": "Test",
                        "title": "Test"
                    },
                    "map": {
                        "layers": [{
                            "source": "1",
                            "name": "No background",
                            "title": "No background",
                            "visibility": false,
                            "opacity": 1,
                            "group": "background",
                            "fixed": true,
                            "selected": false,
                            "type": "OpenLayers.Layer",
                            "args": ["No background"]
                        }, {
                            "source": "2",
                            "name": "mapnik",
                            "title": "OpenStreetMap",
                            "visibility": true,
                            "opacity": 1,
                            "group": "background",
                            "fixed": true,
                            "selected": false
                        }, {
                            "source": "5",
                            "name": "gemeenten",
                            "title": "gemeenten",
                            "visibility": true,
                            "opacity": 1,
                            "selected": false,
                            "capability": {
                                "nestedLayers": [],
                                // "styles": [{
                                //     "name": "bestuurlijkegrenzen:bestuurlijkegrenzen_gemeentegrenzen",
                                //     "title": "gemeenten",
                                //     "legend": { "width": "86", "height": "40", "format": "image/png", "href": "https://geodata.nationaalgeoregister.nl/bestuurlijkegrenzen/wms?request=GetLegendGraphic&format=image%2Fpng&width=20&height=20&layer=gemeenten" }
                                // }],
                                "srs": {
                                    "EPSG:3857": true
                                },
                                // "metadataURLs": [{
                                //     "type": "TC211",
                                //     "format": "text/plain",
                                //     "href": "http://nationaalgeoregister.nl/geonetwork/srv/dut/xml.metadata.get?uuid=c5c4a6d6-b850-473c-8ab5-af9c2c550809"
                                // }],
                                "bbox": {
                                    "EPSG:4326": {
                                        "bbox": [3.2051823668269814, 50.7334127694571, 7.244186283978288, 53.58278517693342],
                                        "srs": "EPSG:4326"
                                    },
                                    "EPSG:4258": {
                                        "bbox": [3.2051823668269814, 50.73341277038118, 7.244186283978288, 53.58278517783418],
                                        "srs": "EPSG:4258"
                                    },
                                    "EPSG:3035": {
                                        "bbox": [3851492.1797789703, 3073614.302509961, 4138450.626227286, 3405033.293444387],
                                        "srs": "EPSG:3035"
                                    },
                                    "EPSG:3034": {
                                        "bbox": [3546541.1842526076, 2668257.571715348, 3823535.927986264, 2988074.0491355434],
                                        "srs": "EPSG:3034"
                                    },
                                    "EPSG:3857": {
                                        "bbox": [356799.268974759, 6574272.316704847, 806419.1283440797, 7091533.451465934],
                                        "srs": "EPSG:3857"
                                    },
                                    "EPSG:28992": {
                                        "bbox": [10425.156, 306846.198, 278026.09, 621876.3],
                                        "srs": "EPSG:28992"
                                    },
                                    "EPSG:25831": {
                                        "bbox": [513590.01161562005, 5620234.96004342, 791375.717212824, 5943906.836550638],
                                        "srs": "EPSG:25831"
                                    },
                                    "EPSG:25832": {
                                        "bbox": [100650.211576448, 5622404.0854928065, 383725.93425894435, 5950552.142101422],
                                        "srs": "EPSG:25832"
                                    }
                                },
                                "llbbox": [3.206235952734017, 50.7336070072307, 7.2452582753351376, 53.58297881371805],
                                "dimensions": {},
                                // "authorityURLs": {
                                //     "PDOK": "http://www.pdok.nl",
                                //     "EZ": "http://www.rijksoverheid.nl/ministeries/ez"
                                // },
                                "identifiers": { "EZ": "nl.ez.1" },
                                "keywords": ["gemeenten", "features"],
                                "queryable": true,
                                "cascaded": 0,
                                "opaque": false,
                                "noSubsets": false,
                                "fixedWidth": 0,
                                "fixedHeight": 0,
                                "name": "gemeenten",
                                "title": "gemeenten",
                                "abstract": "Bestuurlijke Grenzen bestaan uit de gemeente-, provincie- en rijksgrenzen. Deze worden sinds 2012 vervaardigd op basis van de kadastrale registratie (BRK).",
                                "prefix": "gemeenten",
                                "formats": [
                                    "image/png",
                                    "application/atom xml",
                                    "application/atom+xml",
                                    "application/json;type=utfgrid", "application/openlayers", "application/pdf", "application/rss xml", "application/rss+xml", "application/vnd.google-earth.kml", "application/vnd.google-earth.kml xml", "application/vnd.google-earth.kml+xml", "application/vnd.google-earth.kml+xml;mode=networklink", "application/vnd.google-earth.kmz", "application/vnd.google-earth.kmz xml", "application/vnd.google-earth.kmz+xml", "application/vnd.google-earth.kmz;mode=networklink", "atom", "image/geotiff", "image/geotiff8", "image/gif", "image/gif;subtype=animated", "image/jpeg", "image/png8", "image/png; mode=8bit", "image/svg", "image/svg xml", "image/svg+xml", "image/tiff", "image/tiff8", "image/vnd.jpeg-png", "kml", "kmz", "openlayers", "rss", "text/html; subtype=openlayers", "utfgrid"
                                ],
                                "infoFormats": ["text/plain", "application/vnd.ogc.gml", "text/xml", "application/vnd.ogc.gml/3.1.1", "text/xml; subtype=gml/3.1.1", "text/html", "application/json"]
                            },
                            "format": "image/png",
                            "styles": "",
                            "tiled": true,
                            "transparent": true,
                            "attribution": null,
                            "cached": true
                        }],
                        "center": [581609.19865942, 6832902.8840853],
                        "units": "m",
                        "maxResolution": 156543.03390625,
                        "maxExtent": [-20037508.34, -20037508.34, 20037508.34, 20037508.34],
                        "zoom": 7,
                        "projection": "EPSG:900913"
                    },
                    "id": 0,
                    "sources": {
                        "0": {
                            "url": "http://demo.geonode.org/geoserver/wms",
                            "restUrl": "/gs/rest",
                            "ptype": "gxp_wmscsource",
                            "title": "Local Geoserver",
                            "projection": "EPSG:900913",
                            "id": "0",
                            "baseParams": { "SERVICE": "WMS", "REQUEST": "GetCapabilities", "TILED": true, "VERSION": "1.1.1" }
                        },
                        "1": {
                            "ptype": "gxp_olsource",
                            "projection": "EPSG:900913",
                            "id": "1"
                        },
                        "2": {
                            "ptype": "gxp_osmsource",
                            "projection": "EPSG:900913",
                            "id": "2"
                        },
                        "3": {
                            "url": "http://hh.worldmap.harvard.edu/search/csw",
                            "remote": true,
                            "ptype": "gxp_wmscsource",
                            "name": "HHypermap",
                            "projection": "EPSG:900913",
                            "id": "3",
                            "baseParams": { "SERVICE": "WMS", "REQUEST": "GetCapabilities", "TILED": true, "VERSION": "1.1.1" }
                        },
                        "4": {
                            "url": "http://fcortesz.servehttp.com:2005/geoserver/Sam/wms",
                            "remote": true,
                            "ptype": "gxp_wmscsource",
                            "name": "Sample",
                            "projection": "EPSG:900913",
                            "id": "4",
                            "baseParams": { "SERVICE": "WMS", "REQUEST": "GetCapabilities", "TILED": true, "VERSION": "1.1.1" }
                        },
                        "5": {
                            "url": "https://geodata.nationaalgeoregister.nl/bestuurlijkegrenzen/wms",
                            "remote": true,
                            "ptype": "gxp_wmscsource",
                            "name": "Besturrlijke_grenzen",
                            "projection": "EPSG:900913",
                            "id": "5",
                            "baseParams": { "SERVICE": "WMS", "REQUEST": "GetCapabilities", "TILED": true, "VERSION": "1.1.1" },
                            "title": "Bestuurlijke grenzen WMS"
                        },
                        "6": {
                            "url": "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/",
                            "remote": true,
                            "ptype": "gxp_wmscsource",
                            "name": "zhangheng",
                            "projection": "EPSG:900913",
                            "id": "6",
                            "baseParams": { "SERVICE": "WMS", "REQUEST": "GetCapabilities", "TILED": true, "VERSION": "1.1.1" }
                        },
                        "search": {
                            "ptype": "gxp_geonodeapicataloguesource",
                            "restUrl": "/gs/rest",
                            "url": "/api/layers/",
                            "projection": "EPSG:900913",
                            "id": "search"
                        }
                    },
                    // "viewerTools": [{
                    //     "hidden": true,
                    //     "actions": ["layerchooser"],
                    //     "checked": true
                    // }, {
                    //     "hidden": true,
                    //     "actions": ["-"],
                    //     "checked": true
                    // }, {
                    //     "leaf": true,
                    //     "text": "Print map",
                    //     "ptype": "gxp_print",
                    //     "iconCls": "gxp-icon-print",
                    //     "customParams": { "outputFilename": "GeoExplorer-print" },
                    //     "printService": "http://demo.geonode.org/geoserver/pdf/",
                    //     "checked": true
                    // }, {
                    //     "leaf": true,
                    //     "text": "Pan map",
                    //     "checked": true,
                    //     "iconCls": "gxp-icon-pan",
                    //     "ptype": "gxp_navigation",
                    //     "toggleGroup": "navigation"
                    // }, {
                    //     "leaf": true,
                    //     "text": "Get Feature Info",
                    //     "checked": true,
                    //     "iconCls": "gxp-icon-getfeatureinfo",
                    //     "ptype": "gxp_wmsgetfeatureinfo",
                    //     "format": "grid",
                    //     "toggleGroup": "interaction"
                    // }, {
                    //     "leaf": true,
                    //     "text": "Measure",
                    //     "checked": true,
                    //     "iconCls": "gxp-icon-measure-length",
                    //     "ptype": "gxp_measure",
                    //     "controlOptions": { "immediate": true },
                    //     "toggleGroup": "interaction"
                    // }, {
                    //     "leaf": true,
                    //     "text": "Zoom in / Zoom out",
                    //     "checked": true,
                    //     "iconCls": "gxp-icon-zoom-in",
                    //     "ptype": "gxp_zoom"
                    // }, {
                    //     "leaf": true,
                    //     "text": "Zoom to previous extent / Zoom to next extent",
                    //     "checked": true,
                    //     "iconCls": "gxp-icon-zoom-previous",
                    //     "ptype": "gxp_navigationhistory"
                    // }, {
                    //     "leaf": true,
                    //     "text": "Zoom to max extent",
                    //     "checked": true,
                    //     "iconCls": "gxp-icon-zoomtoextent",
                    //     "ptype": "gxp_zoomtoextent"
                    // }, {
                    //     "leaf": true,
                    //     "text": "Show legend",
                    //     "checked": true,
                    //     "iconCls": "gxp-icon-legend",
                    //     "ptype": "gxp_legend"
                    // }, {
                    //     "leaf": true,
                    //     "text": "Switch to 3D Viewer",
                    //     "checked": true,
                    //     "iconCls": "gxp-icon-googleearth",
                    //     "ptype": "gxp_googleearth"
                    // }, {
                    //     "hidden": true,
                    //     "actions": ["->"],
                    //     "checked": true
                    // }, {
                    //     "hidden": true,
                    //     "actions": ["aboutbutton"],
                    //     "checked": true
                    // }]
                }
                mapObj.about.abstract = name;
                mapObj.about.title = name;
                busyStateManager.showBusyState(appMessages.busyState.save);

                return mapRepository.saveAs(mapObj).success(function() {
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