appModule.factory('sldGenerator', ['sldTemplateService', 'strokeDashstyles', 'pointTextGraphics',
    function (sldTemplateService, strokeDashstyles, pointTextGraphics) {

        var types = { point: getPointTemplate, polyline: getPolylineTemplate, polygon: getPolygonTemplate, geoTiff: getRasterTemplate, geoPdf: getRasterTemplate };

        function getPointTemplate(style, includeHeader, classification) {

            var fillOpacity = style.fillOpacity === 0 ? 0.005 : style.fillOpacity; //fix for transparent feature selection problem
            var sld;
            if (style.graphicName) {
                sld = formatString(getSldTemplate(sldTemplateService.simplePointTemplate, includeHeader),
                [
                    style.graphicName, style.strokeColor, style.strokeWidth,
                    strokeDashstyles.getDashedArray(style),
                    style.fillColor, fillOpacity, style.pointRadius,
                    sldTemplateService.wrapWithFilterTag(getClassificationSldFilter(classification))
                ]);
            } else if (style.textGraphicName && !style.textFontAwesome) {
                sld = formatString(getSldTemplate(sldTemplateService.pointTemplateForTextGraphic, includeHeader),
                [
                    pointTextGraphics.getGraphicNameForSld(style.textGraphicName), style.strokeColor, style.strokeWidth,
                    style.fillColor, fillOpacity, style.text, pointTextGraphics.getDisplacementY(style.textGraphicName), style.textFillColor,
                    sldTemplateService.wrapWithFilterTag(getClassificationSldFilter(classification))
                ]);
            } else if (style.textGraphicName && style.textFontAwesome) {
               

                sld = formatString(getSldTemplate(sldTemplateService.pointTemplateForFontAwosomeTextGraphic, includeHeader),
                [
                    pointTextGraphics.getGraphicNameForSld(style.textGraphicName), style.strokeColor, style.strokeWidth,
                    style.fillColor, fillOpacity, style.text, pointTextGraphics.getDisplacementY(style.textGraphicName), style.textFillColor,
                    sldTemplateService.wrapWithFilterTag(getClassificationSldFilter(classification)),entityForSymbolInContainer(style.text)
                ]);
            } else {
                sld = formatString(getSldTemplate(sldTemplateService.pointWithExternalGraphicTemplate, includeHeader),
                [
                    window.location.origin, style.externalGraphic, fillOpacity, style.pointRadius,
                    sldTemplateService.wrapWithFilterTag(getClassificationSldFilter(classification))
                ]);
            }
            return sld;
        }

        function entityForSymbolInContainer(selector) {
            var code = selector.charCodeAt(0);
            var codeHex = code.toString(16).toUpperCase();
            while (codeHex.length < 4) {
                codeHex = "0" + codeHex;
            }

            return "0x" + codeHex + "";
        }
        function getLabelSld(labelConfig, featureType) {
            if (!labelConfig || !labelConfig.attribute) return "";

            if (featureType === "polyline") {
                return formatString(sldTemplateService.labelTemplateForPolyline, [labelConfig.attribute, labelConfig.font, labelConfig.size,
                        labelConfig.fontStyle, labelConfig.fontWeight, labelConfig.offsetY,
                        labelConfig.color, formatString(sldTemplateService.getLabelOutLineTemplate(labelConfig.showBorder), [labelConfig.borderColor]), getLabelingVendorOptions(labelConfig)]);
            }
            return formatString(sldTemplateService.labelTemplateForPointAndPolygon, [labelConfig.attribute, labelConfig.font, labelConfig.size,
                        labelConfig.fontStyle, labelConfig.fontWeight, labelConfig.alignment, labelConfig.offsetX, labelConfig.offsetY,
                        labelConfig.rotation, labelConfig.color, formatString(sldTemplateService.getLabelOutLineTemplate(labelConfig.showBorder), [labelConfig.borderColor]), getLabelingVendorOptions(labelConfig)]);
        }

        function getLabelingVendorOptions(labelConfig) {
            var vendorOptions = '';
            if (labelConfig.repeat) {
                vendorOptions += formatString(sldTemplateService.labelingVendorOptionTemplates.repeat, [labelConfig.repeatInterval]);
            }
            if (labelConfig.followLine) {
                vendorOptions += sldTemplateService.labelingVendorOptionTemplates.followLine;
            }
            if (labelConfig.autoWrap) {
                vendorOptions += formatString(sldTemplateService.labelingVendorOptionTemplates.autoWrap, [labelConfig.wrapPixel]);
            }
            vendorOptions += formatString(sldTemplateService.labelingVendorOptionTemplates.maxDisplacement, [labelConfig.repeat ? labelConfig.repeatInterval - 1 : 100]);

            return vendorOptions /*+ formatString(sldTemplateService.labelingVendorOptionTemplates.resolveConflict, ['false'])*/;
        }

        function getPolylineTemplate(style, includeHeader, classification) {
            var sldTemplateForPolyline = getSldTemplate(sldTemplateService.simplePolylineTemplate, includeHeader);

            return formatString(sldTemplateForPolyline,
            [
                style.strokeColor, style.strokeWidth, strokeDashstyles.getDashedArray(style),
                sldTemplateService.wrapWithFilterTag(getClassificationSldFilter(classification))
            ]);
        }

        function getPolygonTemplate(style, includeHeader, classification) {
            var sldTemplateForPolygon = getSldTemplate(sldTemplateService.simplePolygonTemplate, includeHeader);
            var fillOpacity = style.fillOpacity === 0 ? 0.005 : style.fillOpacity; //fix for transparent feature selection problem
            var fillPatternSld = "";
            if (style.fillPattern) {
                fillPatternSld = formatString(sldTemplateService.fillPatternTemplate, [style.fillPattern, style.fillColor, style.pixelDensity]);
            }

            return formatString(sldTemplateForPolygon,
            [
                style.fillColor, fillOpacity, style.strokeColor, style.strokeWidth,
                strokeDashstyles.getDashedArray(style),
                sldTemplateService.wrapWithFilterTag(getClassificationSldFilter(classification)),
                fillPatternSld
            ]);
        }

        function getRasterTemplate(styles, includeHeader, classification) {
            var sldTemplateForRaster = getSldTemplate(sldTemplateService.simpleRasterTemplate, includeHeader);
            return formatString(sldTemplateForRaster, [styles.opacity, sldTemplateService.wrapWithFilterTag(getClassificationSldFilter(classification))]);
        }

        function getConditionalTemplate(classification) {
            return sldTemplateService.wrapWithNotTag(getClassificationSldFilter(classification));
        }

        function getSldTemplate(templateBody, includeHeader) {
            if (includeHeader) {
                return formatString(sldTemplateService.sldHeader, [templateBody]);
            }
            return templateBody;
        }

        function getClassificationSldFilter(classification) {
            if (!classification) return "";
            if (classification.rangeMin !== undefined && classification.rangeMin !== null) {
                return classification.isFirstClass ? formatString(sldTemplateService.getRangeFilterTemplateForFirstRange(), [classification.attributeName, classification.rangeMin, classification.rangeMax])
                    : formatString(sldTemplateService.getRangeFilterTemplate(), [classification.attributeName, classification.rangeMin, classification.rangeMax]);
            } else {
                if (classification.value !== null && classification.value !== undefined && classification.value !== "") {
                    return formatString(sldTemplateService.getUniqueFilterTemplate(), [classification.attributeName, classification.value]);
                } else {
                    return formatString(sldTemplateService.getUniqueFilterTemplateForNullValue(), [classification.attributeName]);
                }
            }
        }

        function formatString(template, args) {
            for (var i in args) {
                var re = new RegExp("\\{" + i + "\\}", "g");
                template = template.replace(re, args[i]);
            }
            return template;
        }

        function getChartDataString(selectedAttributes,config) {
            var chartDataString = "chd=t:";
            var seriesColor = "chco=";
            for (var index in selectedAttributes) {

                var attrId = selectedAttributes[index].numericAttribute.Id;
                chartDataString += "${" + attrId + "}";

                seriesColor += selectedAttributes[index].attributeColor.slice(1);

                if (index != selectedAttributes.length - 1) {
                    var seriesDataSeparator = config.chartId == 'bvg' ? '|' : ',';
                    chartDataString += seriesDataSeparator;
                    seriesColor += ",";
                }
            }
            return {
                chartDataString: chartDataString,
                seriesColor:seriesColor
            };
        }

        function getChartSizeString(config,sizeAttributeValues) {
            var sum = 0;
            for (var value in sizeAttributeValues) {
                sum += sizeAttributeValues[value];
            }

            var sizeString = formatString(sldTemplateService.chartSizeTemplate, [config.chartSizeAttributeId, sum]);
            return sizeString;
        }

        return {
            formatString: formatString,
            getSld: function (type, styles, includeHeader, classification) {
                return types[type](styles, includeHeader, classification);
            },
            getLabelingSld: getLabelSld,
            getClassificationConditionalSld: getConditionalTemplate,
            getChartSld: function (config,sizeAttributeVaues) {
                var selectedAttributes = _.filter(config.chartAttributeList, function (attribute) { return attribute.checked == true });
                if (selectedAttributes.length == 0) {
                    return "";
                }
                var chartProperties = getChartDataString(selectedAttributes,config);
                var chartSizeString = getChartSizeString(config,sizeAttributeVaues);
                return formatString(sldTemplateService.chartSld(config, chartProperties.chartDataString, chartProperties.seriesColor, chartSizeString));
            },
            getHeatmapSld: function (config) {
                return formatString(sldTemplateService.heatmapTemplate, [config.attributeId, config.radius, config.pixelDensity,
                config.style.low, config.style.mid, config.style.high, config.style.veryHigh]);
            },
            getWeightedPointSld: function (config) {
                var sldStyle = "";
                if (config.classes && config.classes.length > 0) {
                    config.classes[0].isFirstClass = true;
                }
                for (var i in config.classes) {
                    sldStyle += sldTemplateService.wrapWithRuleTag(getPointTemplate(config.classes[i].style, false, config.classes[i], null));
                }
                return formatString(sldTemplateService.weightedPointTemplate, [sldStyle]);
            },
            getColorMapEntryForRange: function (config) {
                var colorMapEntry = "";
                if (config.classes && config.classes.length > 0) {
                    if (config.noData <= config.classes[0].rangeMin) {
                        colorMapEntry = sldTemplateService.makeTransparentColorMapEntryTag("#000000", config.noData);
                    }
                    for (var i in config.classes) {
                        if (config.noData >= config.classes[i].rangeMin && config.noData <= config.classes[i].rangeMax) {
                            colorMapEntry += sldTemplateService.makeTransparentColorMapEntryTag("#000000", config.noData);
                        }
                        colorMapEntry += sldTemplateService.makeColorMapEntryTag(config.style[i], config.classes[i].rangeMax);
                    }
                    if (config.noData >= config.classes[config.classes.length - 1].rangeMax) {
                        colorMapEntry += sldTemplateService.makeTransparentColorMapEntryTag("#000000", config.noData);
                    }
                }
                return colorMapEntry;
            },
            getColorMapEntryForUnique: function (config) {
                var colorMapEntry = "";
                if (config.values) {
                    var length = config.values.length;
                    var selectedValuesLength = _.filter(config.values, function (item) {
                        return item.isSelected;
                    }).length;
                    if (length > 0 && selectedValuesLength > 0) {
                        if (config.noData <= config.values[0].value) {
                            colorMapEntry += sldTemplateService.makeTransparentColorMapEntryTag("#000000", config.noData);
                        }
                        for (var i = 0; i < length - 1; i++) {
                            colorMapEntry += sldTemplateService.makeColorMapEntryTag(config.values[i].color, config.values[i].value);
                            if (config.noData >= config.values[i].value && config.noData <= config.values[i + 1].value) {
                                colorMapEntry += sldTemplateService.makeTransparentColorMapEntryTag("#000000", config.noData);
                            }
                        }
                        colorMapEntry += sldTemplateService.makeColorMapEntryTag(config.values[length - 1].color, config.values[length - 1].value);
                        if (config.noData >= config.values[length - 1].value) {
                            colorMapEntry += sldTemplateService.makeTransparentColorMapEntryTag("#000000", config.noData);
                        }
                    }
                }
                return colorMapEntry;
            },
            getRasterSld: function (opacity, colorMapEntry) {
                var sld = formatString(sldTemplateService.rasterColorTemplate, [opacity, colorMapEntry]);
                return sld;
            }
        }
    }
])