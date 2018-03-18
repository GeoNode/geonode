mapModule.factory('layerService', layerService);

layerService.$inject = [
    '$rootScope', 'layerRepository', 'featureService', 'layerStyleGenerator', 'featureFilterGenerator', 'sldTemplateService', 'interactionHandler', '$q', 'LayerService', 'visualizationService', 'layerRenderingModeFactory', '$window'
];

function layerService($rootScope, layerRepository, featureService, layerStyleGenerator, featureFilterGenerator, sldTemplateService, interactionHandler, $q, newLayerService, visualizationService, layerRenderingModeFactory, $window) {
    function _map(layer, order) {
        if (layer.BoundingBox) {
            layer.bbox = [layer.BoundingBox[0].extent[0],
                layer.BoundingBox[0].extent[1],
                layer.BoundingBox[0].extent[2],
                layer.BoundingBox[0].extent[3]
            ];

        }
        if (!layer.bbox) {
            layer.bbox = [-9818543.41779904, 5183814.6260749, -9770487.95134629, 5235883.07751104];
        }
        if (!layer.hasOwnProperty('visibility'))
            layer.visibility = true;
        // var userStyle = layer.name + '_' + _uuid();
        return {
            "LayerId": layer.Name || layer.name,
            "Name": layer.Name || layer.name,
            "SortOrder": order || 0,
            // "LastUpdateOn": "2017-10-10T11:10:26.083Z",
            "ClassifierDefinitions": {},
            "CanWrite": true,
            // "DataId": "s_facf34ee54914605943fe987f5b3637c",
            // "ShapeType": "point",

            "VisualizationSettings": null,
            "IsVisible": layer.visibility,
            "Filters": [],
            "ZoomLevel": 0,
            "ModificationState": "Added",
            "LayerExtent": {
                "MinX": layer.bbox[0],
                "MinY": layer.bbox[1],
                "MaxX": layer.bbox[2],
                "MaxY": layer.bbox[3]
            },
            "AttributeDefinition": [],
            // "IdColumn": "gid",
            "LinearUnit": "Meter",
            "IsLocked": false,
            "DataSourceName": "illinois_poi",
            "SourceFileExists": true,
            "IsDataOwner": true,
            "IsRaster": false,
            "geoserverUrl": layer.geoserverUrl,
            "Style": newLayerService.getNewStyle()
                // "SavedDataId": "s_fe297a3305394811919f33cdb16fc30d"
        };
    }
    var layerDataType = {};

    function _getPointData(data) {
        return Object.assign({
            'permissions': {},
            'charset': 'UTF-8',
            'layer_title': 'auto_layer_upload_point',
            'category': 'building',
            'organization': 1,
            'csv_layer_type': 'latlon',
            'longitude': 'longitude',
            'lattitude': 'latitude',
            'layer_type': 'csv',
            // 'admin_upload': true
        }, data);
    }

    function _getGeomData(data) {
        return {
            'permissions': {},
            'charset': 'UTF-8',
            'layer_title': 'auto_layer_upload_multi',
            'category': 'building',
            'organization': 1,
            'csv_layer_type': 'the_geom',
            'the_geom': 'geom',
            'layer_type': 'csv',
            // 'admin_upload': true
        };
    }
    layerDataType.Point = _getPointData;
    layerDataType.Geom = _getGeomData;

    var factory = {

        downloadData: function(surfLayer) {
            layerRepository.downloadData(surfLayer.getId());
        },
        saveAttributeDefinitions: function(surfLayer, attributeDefinitions) {
            layerRepository.saveAttributeDefinitions(surfLayer.getId(), attributeDefinitions).success(function(definition) {
                surfLayer.setAttributeDefinition(definition);
                surfLayer.resetLastAttributeDefinitionUpdateTime();
                if (featureService.hasActive()) {
                    surfLayer.tools.selectFeature.innerTool.reloadCurrentFeature();
                }
            });
        },
        saveProperties: function(surfLayer, name, zoomLevel, style, excludeSld, callBack) {
            var defaultStyleSld = excludeSld ? null : layerStyleGenerator.getSldStyle(surfLayer.getFeatureType(),
                style.default, HTMLOptGroupElement, null, style.labelConfig);

            var selectionStyleSld = excludeSld ? null : layerStyleGenerator.getSldStyle(surfLayer.getFeatureType(),
                style.select, HTMLOptGroupElement, null);

            var labelingSld = layerStyleGenerator.getLabelingSld(style.labelConfig, surfLayer.getFeatureType());

            var classificationSlds = getClassificationSld(surfLayer.getFeatureType(), style.classifierDefinitions, excludeSld);
            var reClassifier = new RegExp("\\{classifierSld\\}", "g");
            var reLabel = new RegExp("\\{labelSld\\}", "g");
            var chartSldRegex = new RegExp("<!--chartSld-->", "g");

            defaultStyleSld = defaultStyleSld.replace(reClassifier, classificationSlds.classificationStyle);
            defaultStyleSld = defaultStyleSld.replace(reLabel, labelingSld);

            layerRenderingModeFactory.setLayerRenderingMode(surfLayer);

            if (surfLayer.Style.VisualizationSettings) {
                visualizationService.getVisualizationSld(surfLayer, surfLayer.Style.VisualizationSettings)
                    .then(function(visSld) {
                        if (visualizationService.isChart(surfLayer.Style.VisualizationSettings)) {
                            defaultStyleSld = defaultStyleSld.replace(chartSldRegex, visSld);
                        } else if (visualizationService.isHeatMap(surfLayer.Style.VisualizationSettings)) {
                            defaultStyleSld = visSld;
                        }

                        return doAction();
                    });
            } else {
                return doAction();
            }


            function doAction() {
                surfLayer.setName(name);
                surfLayer.setStyle(style);
                //surfLayer.setTiled(surfLayer.Style.tiled);
                surfLayer.setZoomLevel(zoomLevel);
                if (!style.id) {
                    return layerRepository.createProperties(surfLayer.getId(), surfLayer.getName(), zoomLevel, surfLayer.getStyle(),
                        defaultStyleSld, selectionStyleSld, labelingSld,
                        function(res) {
                            style.id = res.id;
                            style.Name = res.uuid;
                            style.Title = res.title;
                            surfLayer.setStyle(style);

                            if (callBack) {
                                callBack();
                            } else {
                                surfLayer.refresh();
                                $rootScope.$broadcast('refreshSelectionLayer');
                            }
                        });
                }
                return layerRepository.saveProperties(style.id, surfLayer.getId(), surfLayer.getName(), zoomLevel, surfLayer.getStyle(),
                    defaultStyleSld, selectionStyleSld, labelingSld,
                    function() {
                        if (callBack) {
                            callBack();
                        } else {
                            surfLayer.refresh();
                            $rootScope.$broadcast('refreshSelectionLayer');
                        }
                    });
            }

        },
        saveVisibility: function(surfLayer) {
            // layerRepository.saveVisibility(surfLayer.getId(), surfLayer.IsVisible).success(function() {
            //     if (surfLayer.hasClassifierDefinitions()) {
            //         var classes = surfLayer.getClassifierDefinitions().selected;
            //         for (var index in surfLayer.groups) {
            //             surfLayer.groups[index].isChecked = surfLayer.IsVisible;
            //         }
            //         if (!classes || !classes.length) {
            //             return;
            //         }

            //         for (var i in classes) {
            //             surfLayer.setClassVisible(classes[i], surfLayer.IsVisible, true);
            //         }
            //         factory.saveClassifierDefinitions(surfLayer, surfLayer.getClassifierDefinitions(), true, true);
            //         surfLayer.setFilter(featureFilterGenerator.getFilter(surfLayer));
            //     }
            // });
        },
        queryLayer: function(surfLayer, queries) {
            surfLayer.setQuery(queries);

        },
        saveClassVisibility: function(surfLayer, classes) {
            for (var index in classes) {
                surfLayer.setClassVisible(classes[index], classes[index].checked);
            }
            surfLayer.setFilter(featureFilterGenerator.getFilter(surfLayer));
            // factory.saveClassifierDefinitions(surfLayer, surfLayer.getClassifierDefinitions(), true, true);
        },
        saveClassifierDefinitions: function(surfLayer, classifierDefinitions, hideProgress, excludeSld, broadcastUpdate) {
            if (!hideProgress) {
                busyStateManager.showBusyState(appMessages.busyState.apply);
            }
            var classificationSlds = getClassificationSld(surfLayer.getFeatureType(), classifierDefinitions, excludeSld);

            return layerRepository.saveClassifierDefinitions(surfLayer.getId(), classifierDefinitions,
                    classificationSlds.classificationStyle, classificationSlds.defaultStyleCondition)
                .success(function() {
                    surfLayer.setClassifierDefinitions(classifierDefinitions);
                    if (!hideProgress) {
                        surfLayer.refresh();
                        busyStateManager.hideBusyState();
                    }
                    surfLayer.setFilter(featureFilterGenerator.getFilter(surfLayer));
                    if (broadcastUpdate) {
                        $rootScope.$broadcast('classificationChanged', { layer: surfLayer });
                    }
                });
        },
        clearFeatures: function(surfLayer) {
            return layerRepository.clearFeatures(surfLayer.getId()).success(function() {
                featureService.updateClassifier(surfLayer);
                surfLayer.refresh();
                interactionHandler.clearFeatures();
            });
        },
        fetchWMSFeatures: function(params) {
            return layerRepository.getWMS(undefined, params);
        },
        fetchWmsLayers: function(url) {
            var mappedLayer = [];
            return $q(function(resolve, reject) {
                if (!url)
                    resolve(mappedLayer);
                else {
                    layerRepository.getLayers(url).then(function(res) {
                        res.forEach(function(e) {
                            e.geoserverUrl = url;
                            mappedLayer.push(_map(e));
                        }, this);
                        resolve(mappedLayer);
                    });
                }
            });
        },
        fetchLayers: function() {
            var mappedLayer = [];
            var deferred = $q.defer();
            layerRepository.getLayers()
                .then(function(res) {
                    mappedLayer = res.map(function(e) {
                        return _map({
                            Name: e.detail_url.match(/\w+:\w+/)[0],
                            bbox: ol.proj.transformExtent([e.bbox_x0, e.bbox_y0, e.bbox_x1, e.bbox_y1], 'EPSG:4326', 'EPSG:3857'),
                            geoserverUrl: $window.GeoServerHttp2Root + 'wms?access_token=' + $window.mapConfig.access_token
                        });
                    });
                    deferred.resolve(mappedLayer);
                });
            return deferred.promise;
        },
        map: function(layer, order) {
            return _map(layer, order);
        },
        createLayerFromFeature: function(features, data, defaultDataProjection, featureProjection) {
            var deferred = $q.defer();

            var featureType;
            var geoJsonFormat = new ol.format.GeoJSON();
            var wktFormat = new ol.format.WKT();
            var geoJsonFeatures = [];
            features.forEach(function(f) {

                var geoJsonFeature = JSON.parse(geoJsonFormat.writeFeature(f, {
                    defaultDataProjection: defaultDataProjection || 'EPSG:4326',
                    featureProjection: featureProjection || 'EPSG:3857'
                }));

                var wkt = wktFormat.writeFeature(f, {
                    dataProjection: defaultDataProjection || 'EPSG:4326',
                    featureProjection: featureProjection || 'EPSG:3857'
                });
                geoJsonFeature.properties = Object.assign(geoJsonFeature.properties, { 'geom': wkt });
                geoJsonFeatures.push(geoJsonFeature);
            });

            featureType = geoJsonFeatures[0].geometry.type;

            factory.saveGeoJSONLayer(geoJsonFeatures, featureType, data)
                .then(function(res) {
                    var layer_name = res.url.split('/').pop();

                    var layer = factory.map({
                        name: layer_name,
                        geoserverUrl: $window.GeoServerTileRoot + '?access_token=' + $window.mapConfig.access_token
                    });
                    deferred.resolve(layer);

                }, function(error, status) {
                    deferred.reject({ error: error, status: status });

                });
            return deferred.promise;
        },
        saveGeoJSONLayer: function(geoJsonFeatures, featureType, data) {
            featureType = featureType == 'Point' ? 'Point' : 'Geom';

            var csv = geoJsonToCsv(geoJsonFeatures);
            var file = new Blob([csv], { type: 'application/octet-stream' });
            var url = '/layers/upload';
            var param = layerDataType[featureType](data);

            return layerRepository.uploadCsvLayer(param, file, 'over-pass_the_geom.csv');
        }
    };

    function geoJsonToCsv(geoJsonFeatures) {
        var json = [];
        var keys = {};
        var reducer = function(a, e) {
            var data = {};
            data[e] = true;
            return Object.assign(a, data);
        };
        geoJsonFeatures.forEach(function(e) {
            keys = Object.assign(keys, Object.keys(e.properties).reduce(reducer, {}));
            json.push(Object.assign(e.properties, {
                longitude: e.geometry.coordinates[0],
                latitude: e.geometry.coordinates[1]
            }));
        });
        keys = Object.assign(keys, {
            'longitude': true,
            'latitude': true
        });
        return JsonToCsv(json, keys);
    }

    function JsonToCsv(json, keys) {
        var fields = [];
        if (keys) {
            fields = Object.keys(keys);
        } else {
            fields = Object.keys(json[0]);
        }

        var replacer = function(key, value) { return value == null ? '' : value; };
        var csv = json.map(function(row) {
            return fields.map(function(name) {
                return JSON.stringify(row[name], replacer);
            }).join(',');
        });
        csv.unshift(fields.join(','));
        csv = csv.join('\r\n');
        return csv;
    }

    function replaceSpecialCharacters(style) {
        return style.replace(/&/g, '&amp;').replace(/'/g, '&apos;');
    }

    function getClassificationSld(featureType, classifierDefinitions, excludeSld) {
        if (excludeSld) return { classificationStyle: null, defaultStyleCondition: null };
        var sldStyle = "";
        var conditionalSld = "";
        for (var i in classifierDefinitions.selected) {
            var classification = { isFirstClass: i == 0 };
            angular.extend(classification, classifierDefinitions.selected[i]);
            delete classification.style;
            classification.attributeName = classifierDefinitions.selectedField;
            sldStyle += sldTemplateService.wrapWithRuleTag(layerStyleGenerator.getSldStyle(featureType, classifierDefinitions.selected[i].style, false, classification));
            conditionalSld += layerStyleGenerator.getConditionalSld(classification);
        }
        conditionalSld = sldTemplateService.wrapWithFilterTag(sldTemplateService.wrapWithAndTag(conditionalSld));

        sldStyle = replaceSpecialCharacters(sldStyle);
        conditionalSld = replaceSpecialCharacters(conditionalSld);

        return { classificationStyle: sldStyle, defaultStyleCondition: conditionalSld };
    }
    return factory;
}