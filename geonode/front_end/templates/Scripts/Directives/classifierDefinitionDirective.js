appHelperModule.directive('classifierDefinitions', ['featureTypes',
    function(featureTypes) {
        return {
            restrict: 'AE',
            scope: {
                settingsData: '=',
                inputData: '=',
                classifierBinder: '=',
                featureType: '=',
                defaultStyle: '='
            },
            templateUrl: 'static/Templates/classifierDefinitions.html',
            controller: ['$scope', '$http', '$filter', 'attributeDefinitionHelper', 'attributeTypes',
                function($scope, $http, $filter, attributeDefinitionHelper, attributeTypes) {
                    var isChosenPaletteSet = false;
                    function init() {
                        $scope.isPoint = $scope.featureType == featureTypes.point;
                        $scope.isPolyline = $scope.featureType == featureTypes.polyline;
                        $scope.isPolygon = $scope.featureType == featureTypes.polygon;

                        $scope.rampProperty = $scope.isPolyline ? 'strokeColor' : 'fillColor';

                        $scope.Attributes = $scope.inputData.attributes;
                        $scope.layerId = $scope.inputData.layerId;
                        if (!$scope.settingsData) {
                            $scope.settingsData = {};
                        }
                        $scope.NeededAttributes = [];
                        $scope.chosenValuesForGrid = [];

                        $scope.isDirty = undefined;

                        $scope.flags = {
                            isRange: null,
                            field: null,
                            ShowGridAndList: true,
                            division: 5,
                            chosenPalette: {},
                            PropertyData: []
                        };

                        var rangeFunctionalty = new RangeCalculator();
                        $scope.classifierBinder.colorPaletteGenerator = new ColorPaletteGenerator();

                        $scope.paletteItems = $scope.classifierBinder.colorPaletteGenerator.getPaletteData();

                        var maxValueBeforeEditing = undefined;

                        $scope.classificationEditor = {
                            hide: true,
                            styleEditorClass: 'classification-style-editor-container',
                            classificationTable: 'list-of-values'
                        };

                        if (!_.isEmpty($scope.settingsData) && containsSelectedItem()) {
                            setInitialSettings($scope.settingsData);
                        } else {
                            $scope.classifierBinder.classType = createClassType();
                        }
                        if (!isChosenPaletteSet) {
                            isChosenPaletteSet = true;
                            $scope.$watch("flags.chosenPalette", function(val) {
                                if ($scope.settingsData.selected !== undefined) {
                                    $scope.chosenValuesForGrid = $scope.settingsData.selected;
                                    $scope.classifierBinder.classType.setInitialUnselectedItems($scope.settingsData.unselected);
                                    $scope.settingsData.selected = undefined;
                                    return;
                                }

                                $scope.classifierBinder.colorPaletteGenerator.setChosenPalette(val);
                                var colorList = $scope.classifierBinder.colorPaletteGenerator.getColorList($scope.chosenValuesForGrid.length);

                                angular.forEach($scope.chosenValuesForGrid, function(item, index) {
                                    item.style[$scope.rampProperty] = colorList[index];
                                    item.checked = true;
                                });

                            });
                        }

                    }

                    $scope.isLoading = function() {
                        return $scope.classifierBinder.classType.isDataLoading;
                    };

                    $scope.hideStyleProperty = function() {
                        $('#classStyleEditor').removeClass('animate').addClass('animate-reverse');
                    };

                    function showStyleProperties() {
                        $('#classStyleEditor').removeClass('animate-reverse').addClass('animate');
                    }



                    function setInitialSettings(settings) {
                        $scope.flags.isRange = settings.isRange;
                        $scope.classifierBinder.classType = createClassType();
                        $scope.classifierBinder.classType.setInitialSettings(settings, $scope.classifierBinder.colorPaletteGenerator);
                    }

                    $scope.isRange = function() {
                        return $scope.flags.isRange == 'true';
                    };

                    function createClassType() {
                        return $scope.isRange() ? new RangeType($http, $scope, rangeFunctionalty, attributeDefinitionHelper, $filter) : new UniqueType($http, $scope, attributeTypes, $filter);
                    }

                    $scope.radioSelectionChanged = function() {
                        $scope.classifierBinder.classType = createClassType();
                        $scope.classifierBinder.classType.setFieldDropDown();
                        resetData();
                        $scope.classifierBinder.classType.prepareData($scope.classifierBinder.colorPaletteGenerator);
                    };

                    function resetData() {
                        $scope.chosenValuesForGrid = [];
                        $scope.flags.PropertyData = [];
                        $scope.classifierBinder.colorPaletteGenerator.resetColorIndex();
                        $scope.flags.maximum = undefined;
                        $scope.flags.minimum = undefined;
                        $scope.originalData = undefined;
                    };

                    $scope.dropdownSelectionChanged = function() {
                        resetData();
                        if (_.isNull($scope.flags.field)) {
                            return;
                        }
                        $scope.classifierBinder.classType.getPropertyDataFromServer(function() {
                            $scope.classifierBinder.classType.prepareData($scope.classifierBinder.colorPaletteGenerator);
                        });
                    };

                    $scope.divisionChanged = function() {
                        //TODO: remove to rangetype
                        $scope.chosenValuesForGrid = [];
                        $scope.classifierBinder.classType.prepareData($scope.classifierBinder.colorPaletteGenerator);
                    };

                    $scope.saveEditingValue = function(value) {
                        maxValueBeforeEditing = value;
                    };

                    $scope.rangeLimitChanged = function(item) {
                        //TODO: remove to rangetype
                        if (item.rangeMax === maxValueBeforeEditing) {
                            return;
                        }

                        if (item.rangeMax == null)
                            rangeFunctionalty.adjustNullRange($scope.chosenValuesForGrid, item, $scope.flags.maximum);

                        rangeFunctionalty.adjustRange($scope.chosenValuesForGrid, item);
                        $scope.flags.division = $scope.chosenValuesForGrid.length;

                        $scope.classifierBinder.classType.getCount($scope.chosenValuesForGrid, function(data) {

                            for (var k = 0; k < data.length; k++) {
                                $scope.chosenValuesForGrid[k].count = data[k].count;
                            }
                        });
                    };

                    $scope.reverseColorSet = function() {
                        $scope.classifierBinder.classType.reverseColor();
                    };

                    $scope.addSelectionsToGrid = function() {
                        $scope.classifierBinder.classType.addSelectionsToGrid($scope.classifierBinder.colorPaletteGenerator);
                    };

                    $scope.removeToList = function(index) {
                        $scope.classifierBinder.classType.removeItem(index, $scope.classifierBinder.colorPaletteGenerator);
                    };

                    $scope.removeAll = function() {
                        var itemsLength = $scope.chosenValuesForGrid.length;
                        for (var i = 0; i < itemsLength; i++) {
                            $scope.classifierBinder.classType.removeItem(0, $scope.classifierBinder.colorPaletteGenerator);
                        }
                    };



                    $scope.selectClass = function(cls) {
                        $scope.selectedClass = cls;
                        showStyleProperties();
                        $scope.classificationEditor.hide = false;
                        $scope.classificationEditor.styleEditorClass = 'classification-style-editor-container style-editor-shown';
                        $scope.classificationEditor.classificationTable = 'list-of-values classification-table-hidden';
                    };

                    $scope.hideStyleEditor = function() {
                        $scope.classificationEditor.hide = true;
                        $scope.classificationEditor.styleEditorClass = '';
                        $scope.classificationEditor.classificationTable = '';
                    };

                    function getSelectedIndex() {
                        return _.indexOf($scope.chosenValuesForGrid, $scope.selectedClass);
                    }

                    $scope.moveUp = function() {
                        var index = getSelectedIndex();
                        if (!index) return;
                        var upperClass = angular.copy($scope.chosenValuesForGrid[index - 1]);
                        $scope.chosenValuesForGrid[index - 1] = $scope.selectedClass;
                        $scope.chosenValuesForGrid[index] = upperClass;
                    };

                    $scope.moveDown = function() {
                        var index = getSelectedIndex();
                        if (index == $scope.chosenValuesForGrid.length - 1) return;
                        var lowerClass = angular.copy($scope.chosenValuesForGrid[index + 1]);
                        $scope.chosenValuesForGrid[index + 1] = $scope.selectedClass;
                        $scope.chosenValuesForGrid[index] = lowerClass;
                    };

                    $scope.areInputsChecked = function() {
                        for (var index in $scope.flags.PropertyData) {
                            if ($scope.flags.PropertyData[index].checked) return true;
                        }
                        return false;
                    };

                    function containsSelectedItem() {
                        if (!$scope.settingsData.selectedField) return false;
                        for (var i in $scope.Attributes) {
                            if ($scope.Attributes[i].id == $scope.settingsData.selectedField) return true;
                        }
                        return false;
                    }

                    $scope.isUnique = function() {
                        return $scope.flags.isRange == 'false';
                    };

                    $scope.isRange = function() {
                        return $scope.flags.isRange == 'true';
                    };

                    $scope.fillInitialAlias = function(thisClass) {
                        if (thisClass.alias == undefined) {
                            if ($scope.isUnique()) {
                                thisClass.alias = thisClass.value;
                            } else {
                                thisClass.alias = thisClass.rangeMin + ", " + thisClass.rangeMax;
                            }
                        }
                    };

                    $scope.$watch('settingsData', function() {
                        init();
                    });

                    // init();
                }
            ]
        };
    }
]);