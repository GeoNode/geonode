appHelperModule.directive('attributeDefinitionTable', ['attributeTypes',
    function (attributeTypes) {
        return {
            restrict: 'AE',
            templateUrl: 'static/Templates/attributeDefinitions.html',
            controller: ['$scope', function ($scope) {
                $scope.status = { unchanged: 'unchanged', added: 'added', edited: 'edited', deleted: 'deleted' };

                $scope.addFieldModel = {
                    nameValid: false,
                    typeValid: false,
                    precisionValid: false,
                    scaleValid: true,
                    lengthValid: false
                };

                $scope.addingFieldIsValid = function () {
                    return ($scope.addFieldModel.nameValid &&
                        $scope.addFieldModel.Name &&
                        $scope.addFieldModel.typeValid &&
                        $scope.addFieldModel.precisionValid &&
                        $scope.addFieldModel.scaleValid &&
                        $scope.addFieldModel.lengthValid);
                };

                angular.extend($scope, attributeTypes);

                for (var i = 0; i < $scope.attributeDefs.length; i++) {
                    $scope.attributeDefs[i].isValid = true;
                    $scope.attributeDefs[i].alreadyEdited = true;
                    $scope.attributeDefs[i].isEditing = false;
                    $scope.attributeDefs[i].OriginalName = $scope.attributeDefs[i].AttributeName;
                }

                $scope.validateAddingFieldName = function () {
                    $scope.propertiesData.rule1Violated = isNameInvalid($scope.addFieldModel.AttributeName);
                    $scope.propertiesData.rule3Violated = nameExists($scope.addFieldModel.AttributeName);

                    $scope.addFieldModel.nameValid = !$scope.propertiesData.rule1Violated &&
                            !$scope.propertiesData.rule3Violated;
                };

                $scope.validateAddingFieldType = function () {
                    if (!$scope.addFieldModel.Type) {
                        $scope.addFieldModel.typeValid = false;
                        return;
                    }
                    $scope.propertiesData.rule4Violated = !isUniqueSpatialType($scope.addFieldModel);
                    $scope.addFieldModel.typeValid = !$scope.propertiesData.rule4Violated;

                    if ($scope.isTextType($scope.addFieldModel.Type)) {
                        $scope.validateAddingFieldLength();
                        $scope.addFieldModel.precisionValid = $scope.addFieldModel.scaleValid = true;
                    } else if ($scope.isNumericType($scope.addFieldModel.Type)) {
                        $scope.validateAddingFieldPrecision();
                        $scope.validateAddingFieldScale();
                        $scope.addFieldModel.lengthValid = true;
                    } else {
                        $scope.addFieldModel.precisionValid =
                            $scope.addFieldModel.scaleValid =
                            $scope.addFieldModel.lengthValid = true;
                    }
                };

                $scope.validateAddingFieldLength = function () {
                    $scope.addFieldModel.lengthValid = $scope.addFieldModel.Length <= 254
                        && $scope.addFieldModel.Length >= 1;
                };

                $scope.validateAddingFieldPrecision = function () {
                    $scope.addFieldModel.precisionValid = $scope.addFieldModel.Precision <= 32
                        && $scope.addFieldModel.Precision >= 1;
                };

                $scope.validateAddingFieldScale = function () {
                    $scope.addFieldModel.scaleValid = $scope.addFieldModel.Scale <= $scope.addFieldModel.Precision - 2
                        && $scope.addFieldModel.Scale >= 0;
                };

                function nameExists(name) {
                    for (var j = 0; j < $scope.attributeDefs.length; j++) {
                        var attrDef = $scope.attributeDefs[j];
                        if (attrDef.Status != $scope.status.deleted) {
                            if (attrDef.AttributeName == name) {
                                return true;
                            }
                        }
                    }
                    return false;
                }

                function isNameInvalid(name) {
                    return !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name);
                }

                $scope.setEdited = function (attribute) {
                    attribute.Status = $scope.status.edited;
                }

                $scope.setDirty = function() {
                    $scope.propertiesData.isDirty = true;
                }

                $scope.validateField = function (attribute) {

                    resetValidation();
                    $scope.setDirty();

                    $scope.propertiesData.rule1Violated = isNameInvalid(attribute.AttributeName);
                    $scope.propertiesData.rule3Violated = !areNamesUnique(attribute);
                    $scope.propertiesData.rule4Violated = !isUniqueSpatialType(attribute);

                    attribute.isValid = !$scope.propertiesData.rule1Violated;

                    if (attribute.isValid && attribute.OriginalName
                        && attribute.OriginalName != attribute.AttributeName) {
                        $scope.setEdited(attribute);
                        //attribute.Status = $scope.status.edited;
                    } else if (attribute.OriginalName == attribute.AttributeName) {
                        attribute.Status = $scope.status.unchanged;
                    }
                    $scope.validateAddingFieldName();
                };

                $scope.types = $scope.getTypesForFeatureType($scope.nodeData.layer.shapeType, !!$scope.nodeData.layer.linearUnit);

                $scope.remove = function (index) {
                    if ($scope.attributeDefs[index].Status == $scope.status.added) {
                        $scope.attributeDefs.splice(index, 1);
                    } else {
                        $scope.attributeDefs[index].Status = $scope.status.deleted;
                        $scope.attributeDefs[index].isValid = true;
                    }

                    $scope.setDirty();
                    validateAllFields();
                    $scope.validateAddingFieldName();
                    $scope.validateAddingFieldType();
                };

                $scope.add = function () {
                    // removeEditable();
                    var newField = angular.copy($scope.addFieldModel);
                    newField.Status = $scope.status.added;
                    newField.isValid = true;
                    newField.IsPublished = true;
                    $scope.attributeDefs.push(newField);

                    $scope.addFieldModel.AttributeName = '';
                    $scope.addFieldModel.Name = '';
                    $scope.addFieldModel.nameValid = false;
                    $scope.addFieldModel.Type = null;
                    $scope.addFieldModel.typeValid = false;

                    $scope.setDirty();
                };

                function validateAllFields() {
                    for (var ad in $scope.attributeDefs) {
                        if ($scope.attributeDefs[ad].Status != $scope.status.deleted) {
                            $scope.validateField($scope.attributeDefs[ad]);
                        }
                    }
                }

                function areNamesUnique() {
                    var numberOfAttributes = 0;
                    var uniqueKeyObject = {};
                    for (var j = 0; j < $scope.attributeDefs.length; j++) {
                        if ($scope.attributeDefs[j].Status != $scope.status.deleted) {
                            numberOfAttributes++;
                            uniqueKeyObject[$scope.attributeDefs[j].AttributeName.toLowerCase()] = "";
                        }
                    }
                    return Object.keys(uniqueKeyObject).length == numberOfAttributes;
                }

                function isUniqueSpatialType(def) {
                    if (!$scope.isReadOnlyType(def.Type)) {
                        return true;
                    }

                    for (var j = 0; j < $scope.attributeDefs.length; j++) {
                        var otherDef = $scope.attributeDefs[j];
                        if (
                            otherDef != def
                            && otherDef.Status != $scope.status.deleted
                            && otherDef.Type == def.Type) {

                            return false;
                        }
                    }
                    return true;
                }

                $scope.nodeData.invalidField = function () {
                    var length = $scope.attributeDefs.length;

                    for (var j = 0; j < length; j++) {
                        if (!$scope.attributeDefs[j].isValid || $scope.propertiesData.rule3Violated || $scope.propertiesData.rule4Violated) return true;
                    }
                    return false;
                };

                $scope.enableEditing = function (row, key) {
                    if ($scope.isReadonly) return;
                    row[key] = true;
                    $scope.validateField(row);
                };


                $scope.removeEditable = function (item, key) {
                    item[key] = false;
                    item.alreadyEdited = true;
                };


                function resetValidation() {
                    $scope.propertiesData.rule1Violated = false;
                    $scope.propertiesData.rule3Violated = false;
                    $scope.propertiesData.rule4Violated = false;
                }
            }]
        };
    }
]);