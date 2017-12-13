mapModule.factory('layerService', [
    '$rootScope', 'layerRepository', 'featureService', 'layerStyleGenerator', 'featureFilterGenerator', 'sldTemplateService', 'interactionHandler', '$q',
    function($rootScope, layerRepository, featureService, layerStyleGenerator, featureFilterGenerator, sldTemplateService, interactionHandler, $q) {

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
                    style.default, HTMLOptGroupElement, null);

                var selectionStyleSld = excludeSld ? null : layerStyleGenerator.getSldStyle(surfLayer.getFeatureType(),
                    style.select, HTMLOptGroupElement, null);

                var labelingSld = layerStyleGenerator.getLabelingSld(style.labelConfig, surfLayer.getFeatureType());

                surfLayer.setName(name);
                surfLayer.setStyle(style);
                surfLayer.setZoomLevel(zoomLevel);
                return layerRepository.saveProperties(surfLayer.getId(), surfLayer.getName(), zoomLevel, surfLayer.getStyle(),
                    defaultStyleSld, selectionStyleSld, labelingSld,
                    function() {
                        if (callBack) {
                            callBack();
                        } else {
                            surfLayer.refresh();
                            $rootScope.$broadcast('refreshSelectionLayer');
                        }
                    });
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
            fetchWMSFeatures: function(params){
                return layerRepository.getWMS(undefined, params);
            },
            fetchLayers: function(url) {


                return $q(function(resolve, reject) {
                    // layerRepository.getLayerByName('cite:nyc_roads').then(function(res) {
                    //     resolve([{
                    //         "Name": res.name,
                    //         "CanWrite": true,
                    //         "ShapeType": "point",
                    //         "DataSourceName": "test1",
                    //     }])
                    // })
                    if (!url)
                        resolve([]);
                    else {
                        layerRepository.getLayers(url).then(function(res) {
                            console.log(res);
                            res.WMS_Capabilities.Capability.Layer.Layer.forEach(function(e) {
                                e.CanWrite = true;
                                e.geoserverUrl = url;
                            }, this);
                            resolve(res.WMS_Capabilities.Capability.Layer.Layer);
                        });
                    }

                })

                return [{
                    "LayerId": "s_950085eadbd246b5bbea00407c7066d0",
                    "Name": "test1",
                    "SortOrder": 1,
                    "LastUpdateOn": "2017-09-28T11:14:09.068Z",
                    "ClassifierDefinitions": {},
                    "CanWrite": true,
                    "DataId": "s_3a0134358eb84b84967e3d61d7221900",
                    "ShapeType": "point",
                    "Style": {
                        "Name": "s_e4e9502ac60d42ba82adfe9ac5bcf95d",
                        "default": {
                            "fillPattern": null,
                            "textFillColor": "#222026",
                            "text": null,
                            "pixelDensity": null,
                            "strokeDashstyle": "solid",
                            "strokeWidth": 1.0,
                            "strokeColor": "#FFCC99",
                            "strokeOpacity": null,
                            "fillOpacity": 0.75,
                            "fillColor": "#80664c",
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
                    "ModificationState": "Unchanged",
                    "LayerExtent": {
                        "MinX": -2543824.30133067,
                        "MinY": 3522218.26338092,
                        "MaxX": 5733388.6176145,
                        "MaxY": 5439870.42899942
                    },
                    "AttributeDefinition": [],
                    "IdColumn": "gid",
                    "LinearUnit": "metre",
                    "IsLocked": false,
                    "DataSourceName": "test1",
                    "SourceFileExists": true,
                    "IsDataOwner": true,
                    "IsRaster": false,
                    "SavedDataId": "s_843fee180d644202beac1699ae89dc25"
                }]
            }
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
]);