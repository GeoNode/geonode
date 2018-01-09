mapModule.factory('layerService', [
    '$rootScope', 'layerRepository', 'featureService', 'layerStyleGenerator', 'featureFilterGenerator', 'sldTemplateService', 'interactionHandler', '$q', 'LayerService', 'visualizationService', 'layerRenderingModeFactory',
    function($rootScope, layerRepository, featureService, layerStyleGenerator, featureFilterGenerator, sldTemplateService, interactionHandler, $q, newLayerService, visualizationService, layerRenderingModeFactory) {
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
                "IsVisible": layer.visibility || true,
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

                if(surfLayer.Style.VisualizationSettings){
                    visualizationService.getVisualizationSld(surfLayer, surfLayer.Style.VisualizationSettings)
                    .then(function(visSld){
                        if(visualizationService.isChart(surfLayer.Style.VisualizationSettings)){
                            defaultStyleSld = defaultStyleSld.replace(chartSldRegex, visSld);
                        }
                        else if(visualizationService.isHeatMap(surfLayer.Style.VisualizationSettings)){
                            defaultStyleSld = visSld;
                        }
                        
                        return doAction();
                    });
                }
                else{
                    return doAction();
                }
                

                function doAction(){
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
                return;
                layerRepository.saveVisibility(surfLayer.getId(), surfLayer.IsVisible).success(function() {
                    if (surfLayer.hasClassifierDefinitions()) {
                        var classes = surfLayer.getClassifierDefinitions().selected;
                        for (var index in surfLayer.groups) {
                            surfLayer.groups[index].isChecked = surfLayer.IsVisible;
                        }
                        if (!classes || !classes.length) {
                            return;
                        }

                        for (var i in classes) {
                            surfLayer.setClassVisible(classes[i], surfLayer.IsVisible, true);
                        }
                        factory.saveClassifierDefinitions(surfLayer, surfLayer.getClassifierDefinitions(), true, true);
                        surfLayer.setFilter(featureFilterGenerator.getFilter(surfLayer));
                    }
                });
            },
            queryLayer: function(surfLayer, queries) {
                surfLayer.setQuery(queries);

            },
            saveClassVisibility: function(surfLayer, classes) {
                for (var index in classes) {
                    surfLayer.setClassVisible(classes[index], classes[index].checked);
                }
                surfLayer.setFilter(featureFilterGenerator.getFilter(surfLayer));
                factory.saveClassifierDefinitions(surfLayer, surfLayer.getClassifierDefinitions(), true, true);
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
            fetchLayers: function(url) {
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
            map: function(layer, order){
                return _map(layer, order);
            }
        };

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
]);