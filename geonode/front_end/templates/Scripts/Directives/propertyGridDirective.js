appHelperModule.directive('propertyGrid', [
    'attributeValidator', 'featureService', 'surfToastr', 'dirtyManager', 'attributeTypes', 'mapAccessLevel', 'mapTools',
    function (attributeValidator, featureService, surfToastr, dirtyManager, attributeTypes, mapAccessLevel, mapTools) {
        return {
            restrict: 'AE',
            templateUrl: '/static/Templates/propertyGrid.html',
            scope: {
                isDraft: '=',
                options: '='
            },
            controller: ['$scope', '$rootScope','mapAccessLevel',
                function ($scope, $rootScope, mapAccessLevel) {
                    $scope.selectFeatureTool = mapTools.selectFeature;

                    $scope.showProperties = $rootScope.showProperties;
                    var propertyValueName = 'value';

                    angular.extend($scope, attributeTypes);

                    $scope.prev = function () {
                        $scope.selectFeatureTool.selectPrevious();
                    };

                    $scope.next = function () {
                        $scope.selectFeatureTool.selectNext();
                    };


                    $scope.getFeature = function () {
                        return featureService.getActive();
                    };

                    $scope.hasFeature = function () {
                        return featureService.hasActive();
                    };

                    $scope.isReadonly = function () {
                        if (featureService.hasActive()) {
                            return !featureService.getActive().layer.isWritable();
                        }
                        return false;
                    }

                    $scope.getProperties = function () {
                        return featureService.getActive().getAttributesWithType();
                    };

                    $scope.isAttributeEditable = function () {
                        return featureService.isAttributeEditable();
                    }

                    $scope.toggleAttributeEditableState = function () {
                        featureService.setAttributeEditableState(!featureService.isAttributeEditable());
                    }

                    $scope.attribute = { isLocked: true };
                    $scope.data = { loading: true };

                    var unmodifiedState = {};
                    var unmodifiedStateForValidation = {};

                    $scope.currentEditingIndex = 0;

                    $scope.makeCurrentFieldUneditable = function (property) {
                        if (property.value != unmodifiedState.value) {
                            addToUndoList(unmodifiedState);
                            featureService.saveAttributes([$scope.getFeature()]);
                        }
                        property.isEditing = false;
                        if (property.type != 'Text' && (property.value == '-' || property.value == '.')) {
                            property.value = unmodifiedState.value = "";
                        }
                    };

                    $scope.canDisplayRow = function (property) {
                        if (mapAccessLevel.isPublic) {
                            return property.isPublished;
                        } else {
                            return true;
                        }
                    }

                    $scope.isReadOnlyType = function (property) {
                        return attributeTypes.isReadOnlyType(property.type);
                    };

                    $scope.showUnit = function(property) {
                        return attributeTypes.hasUnit(property.type);
                    };

                    $scope.makeEditable = function (property) {
                        if (!mapAccessLevel.isWritable || $scope.isReadOnlyType(property)) {
                            return;
                        }
                        if (!$scope.isAttributeEditable()) {
                            surfToastr.info(appMessages.toastr.unlockAttributeTable());
                            return;
                        }
                        property.isEditing = true;
                        unmodifiedState = angular.copy(property);
                        unmodifiedStateForValidation = angular.copy(property);
                    };

                    $scope.validate = function (property) {
                        var isValid = false;
                        if ($scope.isNumericType(property.type)) {
                            isValid = attributeValidator.validateNumber(property, unmodifiedStateForValidation, propertyValueName, property.precision, property.scale);
                        } else if($scope.isTextType(property.type)) {
                            isValid = attributeValidator.validateText(property, unmodifiedStateForValidation, propertyValueName, property.length);
                        }
                        $rootScope.attributeTableOptions.isDirty = $rootScope.attributeTableOptions.isDirty || isValid;
                    };
                    
                    $scope.makeDirty = function () {
                        $rootScope.attributeTableOptions.isDirty = true;
                    };

                    function addToUndoList(state) {
                        featureService.addUndoState(angular.copy(state));
                    }

                    function addToRedoList(state) {
                        featureService.addRedoState(angular.copy(state));
                    }

                    function restoreState(state) {
                        var item = getPropertyById(state.id);
                        item.value = state.value;
                    }

                    function getPropertyById(id) {
                        return _.findWhere($scope.getProperties(), { id: id }) || {};
                    }

                    $scope.undo = function () {
                        $rootScope.attributeTableOptions.isDirty = true;
                        var undoState = featureService.getUndoState();
                        addToRedoList(getPropertyById(undoState.id));
                        restoreState(undoState);
                        featureService.saveAttributes([$scope.getFeature()]);
                        dirtyManager.setDirty(true);
                    };

                    $scope.redo = function () {
                        $rootScope.attributeTableOptions.isDirty = true;
                        var redoState = featureService.getRedoState();
                        addToUndoList(getPropertyById(redoState.id));
                        restoreState(redoState);
                        featureService.saveAttributes([$scope.getFeature()]);
                        dirtyManager.setDirty(true);
                    };

                    $scope.enableUndo = function () {
                        return featureService.hasUndoState();
                    };

                    $scope.enableRedo = function () {
                        return featureService.hasRedoState();
                    };
                }]
        };
    }
]);