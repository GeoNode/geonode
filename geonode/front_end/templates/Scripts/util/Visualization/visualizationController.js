appModule.controller('visualizationController', ['$scope', '$modalInstance', 'visualizationService',
    'attributeDefinitionHelper', 'surfLayer',
    function ($scope, $modalInstance, visualizationService, attributeDefinitionHelper, surfLayer) {
        function setSelectedOption() {
            $scope.colorRamp = {};
            var visualizationSettings = surfLayer.VisualizationSettings;
            if (!visualizationSettings) return;

            var item = _.findWhere($scope.settings, { name: visualizationSettings.name });
            for (var i in item) {
                item[i] = $scope.option.selected[i];
            }
            $scope.option.selected = item;
        };

        function setSelectedStyle() {
            $scope.choroplethStyles = visualizationService.getChoroplethStyles();
            if (!$scope.option.selected) return;

            var item = _.findWhere($scope.choroplethStyles, $scope.option.selected.style);
            $scope.option.selected.style = item;
        };

        function init() {
            $scope.service = visualizationService;
            $scope.visualizationTypes = visualizationService.getVisualizationTypes();
            $scope.settings = visualizationService.getDefaultVisualizationSettings(surfLayer);

            $scope.numericAttributes = attributeDefinitionHelper.getNumericAndSpatialAttributeDefs(surfLayer.getAttributeDefinition());
            $scope.heatmapStyles = visualizationService.getHeatmapStyles();
            $scope.option = { selected: surfLayer.VisualizationSettings };


            setSelectedOption();
            setSelectedStyle();

            $scope.colorPaletteGenerator = new ColorPaletteGenerator();
            $scope.paletteItems = $scope.colorPaletteGenerator.getPaletteData();

            if ($scope.option.selected && $scope.option.selected.colorPaletteState) {
                $scope.colorRamp.chosenPalette = $scope.colorPaletteGenerator.getItemAt($scope.option.selected.colorPaletteState.lastColorPaletteIndex);
            } else {
                $scope.colorRamp.chosenPalette = $scope.colorPaletteGenerator.getItemAt(0);
            }
            $scope.colorPaletteGenerator.setChosenPalette($scope.colorRamp.chosenPalette);

        };

        init();

        $scope.initializeAttributeListItemForChart = function () {
            var mustIncludeAttributes = [];
            for (var attr in $scope.numericAttributes) {
                var numericAttribute = $scope.numericAttributes[attr];

                var include = true;

                for (var i in $scope.option.selected.chartAttributeList) {
                    if (numericAttribute.Id === $scope.option.selected.chartAttributeList[i].numericAttribute.Id) {
                        include = false;
                        break;
                    }
                }
                if (include) {
                    mustIncludeAttributes.push({
                        numericAttribute: numericAttribute,
                        checked: false,
                        attributeColor: attributeDefinitionHelper.getRandomColorCode()
                    });
                }
            }

            $scope.option.selected.chartAttributeList = $scope.option.selected.chartAttributeList.concat(mustIncludeAttributes);


            /*if ($scope.option.selected.chartAttributeList.length == 0) {
                $scope.option.selected.chartAttributeList = [];
                for (var index in $scope.numericAttributes) {
                    $scope.option.selected.chartAttributeList.push({
                        numericAttribute: $scope.numericAttributes[index],
                        checked: true,
                        attributeColor: attributeDefinitionHelper.getRandomColorCode()
                    });
                }
            }*/

            $scope.setSelectedAttribute();
        }


        $scope.checkAllAttributeForChart = function () {
            for (var index in $scope.option.selected.chartAttributeList) {
                $scope.option.selected.chartAttributeList[index].checked = $scope.option.selected.isCheckedAllAttribute;
            }
        }


        $scope.transparencyChanged = function () {
            $scope.option.selected.opacity = (100 - $scope.option.selected.transparency) / 100;
        }

        $scope.setSelectedAttribute = function () {
            if ($scope.option.selected && $scope.numericAttributes.length > 0)
                $scope.option.selected.attributeId = $scope.option.selected.attributeId ? $scope.option.selected.attributeId : $scope.numericAttributes[0].Id;
        };

        $scope.setSelectedChartSizeAttribute = function () {
            if ($scope.option.selected && $scope.numericAttributes.length > 0)
                $scope.option.selected.chartSizeAttributeId = $scope.option.selected.chartSizeAttributeId ? $scope.option.selected.chartSizeAttributeId : $scope.numericAttributes[0].Id;
        };

        $scope.close = function () {
            $modalInstance.close();
        };

        $scope.applyVisualization = function () {
            visualizationService.saveVisualization(surfLayer, $scope.option.selected);
            $modalInstance.close();
        };

        $scope.hasCheckedValue = function () {
            for (var index in $scope.option.selected.values) {
                if ($scope.option.selected.values[index].checked) return true;
            }
            return false;
        };

        $scope.hasUnselectedValues = function () {
            for (var index in $scope.option.selected.values) {
                if (!$scope.option.selected.values[index].isSelected) return true;
            }
            return false;
        };

        $scope.hasSelectedValues = function () {
            for (var index in $scope.option.selected.values) {
                if ($scope.option.selected.values[index].isSelected) return true;
            }
            return false;
        }

        $scope.addSelectionsToGrid = function () {
            transformData();
            setColorForGridData();
        }

        function transformData() {
            angular.forEach($scope.option.selected.values, function (item) {
                if (item.checked) {
                    item.checked = false;
                    item.isSelected = true;
                }
            });
        }

        function setColorForGridData() {
            var items = $scope.getSelectedValues();
            var colorList = $scope.colorPaletteGenerator.getColorList(items.length);

            if ($scope.option.selected.isReverse) {
                angular.forEach(items, function (item, index) {
                    item.color = colorList[items.length - index - 1];
                });
            } else {
                angular.forEach(items, function (item, index) {
                    item.color = colorList[index];
                });
            }
        }

        $scope.removeChosenItem = function (item) {
            item.checked = false;
            item.isSelected = false;

            setColorForGridData();
        }

        $scope.removeAll = function () {
            angular.forEach($scope.option.selected.values, function (item) {
                item.checked = false;
                item.isSelected = false;
            });
        }

        $scope.$watch("colorRamp.chosenPalette", function (val) {
            if (val && $scope.option.selected) {
                $scope.colorPaletteGenerator.setChosenPalette(val);
                $scope.option.selected.colorPaletteState = $scope.colorPaletteGenerator.getState();

                setColorForGridData();
            }
        });

        $scope.reverseColorSet = function () {
            $scope.option.selected.isReverse = !$scope.option.selected.isReverse;
            setColorForGridData();
        }

        $scope.getSelectedValues = function () {
            return _.filter($scope.option.selected.values, function (value) {
                return value.isSelected;
            });
        };

        $scope.isLoading = function () {
            return surfLayer.isVisualizationDataLoading;
        }
    }
]);
