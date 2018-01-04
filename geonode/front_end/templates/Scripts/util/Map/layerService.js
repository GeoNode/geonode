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
                    style.default, HTMLOptGroupElement, null, style.labelConfig);

                var selectionStyleSld = excludeSld ? null : layerStyleGenerator.getSldStyle(surfLayer.getFeatureType(),
                    style.select, HTMLOptGroupElement, null);

                var labelingSld = layerStyleGenerator.getLabelingSld(style.labelConfig, surfLayer.getFeatureType());

                var classificationSlds = getClassificationSld(surfLayer.getFeatureType(), style.classifierDefinitions, excludeSld);
                var reClassifier = new RegExp("\\{classifierSld\\}", "g");
                var reLabel = new RegExp("\\{labelSld\\}", "g");

                defaultStyleSld = defaultStyleSld.replace(reClassifier, classificationSlds.classificationStyle);
                defaultStyleSld = defaultStyleSld.replace(reLabel, labelingSld);

                surfLayer.setName(name);
                surfLayer.setStyle(style);
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
                return $q(function(resolve, reject) {
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
                });
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