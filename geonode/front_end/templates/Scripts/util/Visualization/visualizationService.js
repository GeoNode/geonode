appModule.factory('visualizationService', ['urlResolver', 'layerRepository', 'sldGenerator', 'sldTemplateService', 'layerStyleGenerator', 'layerRenderingModeFactory', 'dirtyManager', 'interactionHandler', 'mapModes', 'utilityService', '$q',
    function (urlResolver, layerRepository, sldGenerator, sldTemplateService, layerStyleGenerator, layerRenderingModeFactory, dirtyManager, interactionHandler, mapModes, utilityService, $q) {
        var visualizationFolder = "Content/visualization/";
        var visualizationTypes = { heatmap: 'Heatmap', weightedPoint: 'Weighted Point', choropleth: 'Choropleth', rasterBand: 'Raster Band', chart:'Chart' };

        function getWeightedPointSld(config, layer) {
            var style = angular.copy(layer.getDefaultStyle());

            for (var i = 0; i < config.kindOfPoints; i++) {
                config.classes[i].isFirstClass = i == 0;
                config.classes[i].attributeName = config.attributeId;

                config.classes[i].style = angular.copy(style);
                config.classes[i].style.pointRadius += ((i + 1) * config.differentiationPixel);
            }
            return sldGenerator.getWeightedPointSld(config);
        }

        function getChoroplethSld(config, layer) {
            var sldStyle = "";
            var style = angular.copy(layer.getDefaultStyle());
            style.externalGraphic = null;
            style.graphicName = 'circle';

            for (var i = 0; i < config.classes.length; i++) {
                config.classes[i].isFirstClass = i == 0;
                config.classes[i].attributeName = config.attributeId;

                config.classes[i].style = angular.copy(style);
                if (layer.ShapeType == "polyline") {
                    config.classes[i].style.strokeColor = config.style[i];
                } else {
                    config.classes[i].style.fillColor = config.style[i];
                }
                sldStyle += sldTemplateService.wrapWithRuleTag(layerStyleGenerator.getSldStyle(layer.ShapeType, config.classes[i].style, false, config.classes[i]));
            }
            return sldTemplateService.wrapWithSldHeader(sldStyle);
        }

        var factory = {
            getDefaultVisualizationSettings: function (layer) {
                if (layer.ShapeType == 'point') {
                    return [
                        {
                            name: visualizationTypes.heatmap,
                            attributeId: null,
                            radius: 10,
                            pixelDensity: 10,
                            opacity: 0.5,
                            style: null
                        },
                        {
                            name: visualizationTypes.weightedPoint,
                            attributeId: null,
                            kindOfPoints: 5,
                            differentiationPixel: 5
                        },
                        {
                            name: visualizationTypes.choropleth,
                            attributeId: null,
                            divisions: 5,
                            style: null,
                            algorithm: factory.choroplethAlgorithms[0].value,
                        }
                    ];
                } else if (layer.ShapeType == 'polyline' || layer.ShapeType == 'polygon') {
                    return [
                        // {
                        //     name: visualizationTypes.choropleth,
                        //     attributeId: null,
                        //     divisions: 5,
                        //     style: null,
                        //     algorithm: factory.choroplethAlgorithms[0].value,
                        // },
                        {
                            name: visualizationTypes.chart,
                            chartId: factory.chartTypes[0].value,
                            chartAttributeList: [],
                            chartSizeAttributeId : null,
                            isCheckedAllAttribute: false
                        }
                    ];
                } else if (layer.ShapeType == 'geoTiff' || layer.ShapeType == 'geoPdf') {
                    var settings = {
                        name: visualizationTypes.rasterBand,
                        style: null,
                        isSingleBandedLayer: false,
                        transparency: 0,
                        opacity: 1,
                        isRange: undefined,
                        values: undefined,
                        colorPaletteState: {
                            lastColorPaletteIndex: 0,
                            lastColorIndex: 0
                        },
                        isReverse: false,
                        isLargeDataset: true
                    };
                    layerRepository.isSingleBanded(layer.getId()).success(function (data) {
                        settings.isSingleBandedLayer = data.IsSingleBanded;
                        if (data.IsSingleBanded && !settings.values) {
                            layer.isVisualizationDataLoading = true;
                            layerRepository.getUniqueRasterValues(layer.getId()).success(function (values) {
                                if (values.length <= 50) {
                                    settings.isLargeDataset = false;
                                    settings.values = values;
                                }
                                layer.isVisualizationDataLoading = false;
                            });
                        }
                    });
                    return [
                      settings
                    ];
                }
            },
            choroplethAlgorithms: [
                    {
                        name: 'Equal Interval',
                        value: 'Equal Interval'
                    }
                    //,{
                    //    name: 'Quantile',
                    //    value: 'Quantile'
                    //},
                    //{
                    //    name: 'Jenk',
                    //    value: 'Jenk'
                    //}
            ],
            chartTypes:[
                {
                    name:'Bar Chart',
                    value:'bvg'
                },
                {
                    name:'Horizontal Bar Chart',
                    value:'bhg'
                },
                {
                    name:'Stack Bar Chart',
                    value:'bvs'
                },
                {
                    name: 'Pie Chart',
                    value:'p'
                }
            ],
            getHeatmapStyles: function () {
                return [
                    {
                        styleUrl: urlResolver.resolveRoot(visualizationFolder + "style1.PNG"),
                        colors: { low: '#FFFFFF', mid: '#4444FF', high: '#FFFF00', veryHigh: '#FF0000' }
                    }
                ];
            },
            getChoroplethStyles: function () {
                return Jantrik.gradientGenerator.getVisualizationColorPalettes();
            },
            isChart: function(config){
                return config.name === visualizationTypes.chart;
            },
            isHeatMap: function(config){
                return config.name === visualizationTypes.heatmap;
            },
            saveVisualization: function (layer, config) {
                if (!config || (layer.ShapeType != 'geoTiff' && layer.ShapeType != 'geoPdf' && !config.attributeId)) {
                    return factory.saveVisualizationSettingWithSld(layer, null, "");
                }

                switch (config.name) {
                    case visualizationTypes.heatmap:
                        return saveHeatmap(config, layer);
                    case visualizationTypes.weightedPoint:
                        return saveWeightedPoint(config, layer);
                    case visualizationTypes.choropleth:
                        return saveChoropleth(config, layer);
                    case visualizationTypes.rasterBand:
                        return saveRasterBandColor(config, layer);
                    case visualizationTypes.chart:
                        return saveChartProperties(config, layer);
                }
            },
            getVisualizationSld: function (layer, config) {
                var q = $q.defer();
                if (!config || (layer.ShapeType != 'geoTiff' && layer.ShapeType != 'geoPdf' && !config.attributeId)) {
                    return factory.saveVisualizationSettingWithSld(layer, null, "");
                }
                switch (config.name) {
                    case visualizationTypes.heatmap:
                        var sld = sldGenerator.getHeatmapSld(config);
                        q.resolve(sld);
                        break;
                    case visualizationTypes.weightedPoint:
                        return saveWeightedPoint(config, layer);
                    case visualizationTypes.choropleth:
                        return saveChoropleth(config, layer);
                    case visualizationTypes.rasterBand:
                        return saveRasterBandColor(config, layer);
                    case visualizationTypes.chart:
                        layerRepository.getColumnValues(layer.getId(), config.chartSizeAttributeId)
                        .success(function(data) {
                            var selectedAttributes = utilityService.getChartSelectedAttributes(config);
                            var selectedAttributeIds = _.map(selectedAttributes, function(item){ return item.numericAttribute.Id;});
                            if (selectedAttributes.length == 0) {
                                q.resolve("");
                            }
                            else{
                                var attributeValues = data.values;
                                layerRepository.getColumnMinMaxValues(layer.getId(), selectedAttributeIds)
                                .then(function(data){
                                    var sld = sldGenerator.getChartSld(config, attributeValues, data.data);
                                    q.resolve(sld);
                                });
                            }
                        });
                        break;
                        //return saveChartProperties(config, layer);
                }
                return q.promise;  
            },
            saveVisualizationRenderingMode: function (layer, settings, sldStyle) {
                //layer.style.VisualizationSettings = settings;
                layerRenderingModeFactory.setLayerRenderingMode(layer);
                interactionHandler.setMode(mapModes.select);
                //layer.refresh();
                dirtyManager.setDirty(true);
            },
            saveVisualizationSettingWithSld: function (layer, settings, sldStyle) {
                layer.style.VisualizationSettings = settings;
                layerRenderingModeFactory.setLayerRenderingMode(layer);
                interactionHandler.setMode(mapModes.select);
                //layer.refresh();
                dirtyManager.setDirty(true);
                // return layerRepository.saveVisualizationSettings(layer.getId(), settings, sldStyle).success(function () {
                //     layer.style.VisualizationSettings = settings;
                //     layerRenderingModeFactory.setLayerRenderingMode(layer);
                //     interactionHandler.setMode(mapModes.select);
                //     layer.refresh();
                //     dirtyManager.setDirty(true);
                // });
            },
            getAttributeValueRange: function (layerId, attributeId) {
                return layerRepository.getAttributeValueRange(layerId, attributeId);
            },
            getRasterBandValue: function (layerId) {
                return layerRepository.getRasterBandValue(layerId);
            },
            getRanges: function (minimum, maximum, divisions) {
                var difference = (maximum - minimum) / divisions;
                var classes = [];
                for (var i = 0; i < divisions; i++) {
                    if (i == 0) {
                        classes.push({ rangeMin: minimum, rangeMax: minimum + difference });
                    } else if (i == divisions - 1) {
                        classes.push({ rangeMin: classes[i - 1].rangeMax, rangeMax: maximum });
                    } else {
                        classes.push({ rangeMin: classes[i - 1].rangeMax, rangeMax: classes[i - 1].rangeMax + difference });
                    }
                }
                return classes;
            },
            getVisualizationTypes: function () {
                return visualizationTypes;
            }
        };

        function saveHeatmap(config, layer) {
            factory.saveVisualizationSettingWithSld(layer, config, sldGenerator.getHeatmapSld(config));
        }

        function saveChartProperties(config, layer) {
            layerRepository.getColumnValues(layer.getId(), config.chartSizeAttributeId)
                .success(function(data) {
                    factory.saveVisualizationSettingWithSld(layer, config, sldGenerator.getChartSld(config,data.arrtibuteValues));
                    });
            
        }

        function saveWeightedPoint(config, layer) {
            factory.getAttributeValueRange(layer.getId(), config.attributeId)
                .success(function (data) {
                    var ranges = factory.getRanges(data.minimum, data.maximum, config.kindOfPoints);
                    config.classes = ranges;
                    factory.saveVisualizationSettingWithSld(layer, config, getWeightedPointSld(config, layer));
                });
        }

        function saveChoropleth(config, layer) {
            layerRepository.getRanges(layer.DataId, config.attributeId, config.divisions, config.algorithm)
                .success(function (data) {
                    config.classes = data;
                    factory.saveVisualizationSettingWithSld(layer, config, getChoroplethSld(config, layer));
                });
        }

        function saveRasterBandColor(config, layer) {
            factory.getRasterBandValue(layer.getId()).success(function (data) {
                config.noData = data.noData;

                var colorMapEntry = getColorMapEntry(config, data);
                var sld = sldGenerator.getRasterSld(config.opacity, colorMapEntry);
                factory.saveVisualizationSettingWithSld(layer, config, sld);
            });
        }

        function getColorMapEntry(config, data) {
            var colorMapEntry = "";
            if (config.isRange === 'true') {
                colorMapEntry = getColorMapEntryForRange(config, data);
            } else if (config.isRange === 'false') {
                colorMapEntry = getColorMapEntryForUnique(config);
            }
            return colorMapEntry;
        }

        function getColorMapEntryForRange(config, data) {
            if (config.style && config.style.length > 0) {
                config.classes = factory.getRanges(data.minimum, data.maximum, config.style.length);
            }

            return sldGenerator.getColorMapEntryForRange(config);
        }

        function getColorMapEntryForUnique(config) {
            angular.forEach(config.values, function (item) {
                if (!item.isSelected) {
                    item.color = '#000000';
                }
            });
            return sldGenerator.getColorMapEntryForUnique(config);
        }

        return factory;
    }]);
