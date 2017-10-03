var appHelperModule = angular.module("app.helpers", ['app.filters', 'surfToastr']);

appHelperModule.factory('attributeTypes', [
    'defaultDateFormat',
    'defaultDateTimeFormat',
    '$filter',
    function (defaultDateFormat, defaultDateTimeFormat, $filter) {
        var commonTypes = [
            { type: "text", viewLabel: 'Text' },
            { type: "date", viewLabel: 'Date' },
            { type: 'number', viewLabel: 'Number' },
            { type: 'createdat', viewLabel: 'Created At' }
        ];
        var typeNames = {};

        var types = {
            'point': [{ type: "ycoordinate", viewLabel: "Latitude" }, { type: "xcoordinate", viewLabel: "Longitude" }].concat(commonTypes),
            'polyline': [{ type: "length", viewLabel: "Length" }].concat(commonTypes),
            'polygon': [{ type: "area", viewLabel: "Area" }].concat(commonTypes)
        };

        var spatialTypeSet = { "ycoordinate": true, "xcoordinate": true, "length": true, "area": true };
        var unitFulTypeSet = { "length": true, "area": true };
        var readOnlyTypeSet = { "ycoordinate": true, "xcoordinate": true, "length": true, "area": true, "createdat": true };

        angular.forEach(types, function (array) {
            array.forEach(function (type) {
                typeNames[type.type] = type.viewLabel;
            });
        });

        var factory = {
            getTypesForFeatureType: function (featureType, isLinear) {
                if (isLinear || featureType == 'point') {
                    return types[featureType];
                } else {
                    return commonTypes;
                }
            },
            isReadOnlyType: function (typeName) {
                return !!readOnlyTypeSet[typeName];
            },
            hasUnit: function (typeName) {
                return !!unitFulTypeSet[typeName];
            },
            getViewLabel: function (typeName) {
                return typeNames[typeName] || typeName;
            },
            isNumericType: function (type) {
                return type === 'number';
            },
            isDateType: function (type) {
                return type === 'date';
            },
            isTextType: function (type) {
                return type === 'text';
            },
            isCreatedAtType: function (type) {
                return type === 'createdat';
            },
            isSpatialType: function (type) {
                return !!spatialTypeSet[type];
            },
            toTypedValue: function (type, rawValue) {
                var typedValue = '';
                if (!rawValue) {
                    typedValue = '';
                } else if (factory.isDateType(type)) {
                    typedValue = $filter('date')(rawValue, defaultDateFormat);
                } else if (factory.isCreatedAtType(type)) {
                    typedValue = $filter('date')(rawValue, defaultDateTimeFormat);
                } else if (factory.isNumericType(type) || factory.isSpatialType(type)) {
                    typedValue = isNaN(rawValue) ? '' : parseFloat(rawValue);
                } else if (factory.isTextType(type)) {
                    typedValue = rawValue.toString();
                }
                return typedValue;
            }
        };

        return factory;
    }
]);

appHelperModule.factory('attributeDefinitionHelper', ['attributeTypes',
    function (attributeTypes) {
        function getSpecificTypeDefs(attributeDefs, comparators) {
            var passedAttributeDefs = [];
            for (var i in attributeDefs) {
                var type = attributeDefs[i].Type || attributeDefs[i].type;
                for (var comparator in comparators) {
                    if (comparators[comparator](type)) {
                        passedAttributeDefs.push(attributeDefs[i]);
                        break;
                    }
                }
            }
            return passedAttributeDefs;
        }
        function getRandomColor() {
            var letters = '0123456789ABCDEF';
            var color = '#';
            for (var i = 0; i < 6; i++) {
                color += letters[Math.floor(Math.random() * 16)];
            }
            return color;
        }
        var factory = {
            getNumericAttributeDefs: function (attributeDefs) {
                return getSpecificTypeDefs(attributeDefs, [attributeTypes.isNumericType]);
            },
            getSpatialAttributeDefs: function (attributeDefs) {
                return getSpecificTypeDefs(attributeDefs, [attributeTypes.isSpatialType]);
            },
            getNumericAndSpatialAttributeDefs: function (attributeDefs) {
                return getSpecificTypeDefs(attributeDefs, [attributeTypes.isNumericType, attributeTypes.isSpatialType]);
            },
            getRandomColorCode: function() {
                return getRandomColor();
            }
        };
        return factory;
    }]);

appHelperModule.directive('cogs', [function () {
    return {
        restrict: 'AE',
        template: '<i class="fa fa-cog fa-spin" style="font-size: 23px;"></i>' +
                  '<sup class="fa fa-cog fa-spin-reverse" style="margin-left: -4px; vertical-align: text-top;"></sup>' +
                  '<sub class="fa fa-cog fa-spin-reverse" style="margin-left: -13px; vertical-align: text-bottom;"></sub>'
    }
}]);

appHelperModule.factory('cqlFilterCharacterFormater', [
    function () {
        return {
            formatSpecialCharacters: function (style) {
                return style.toString().replace(/'/g, '\'\'');
            }
        }
    }
]);

appHelperModule.directive('scrollablePane', [
    function () {
        return {
            restrict: 'C',
            link: function (scope, elem, attrs, controller) {

                $(window).resize(function () {
                    resizeScrollableContent();
                });

                $(document).ready(function () {
                    resizeScrollableContent();
                });

                function resizeScrollableContent() {
                    elem.css({ 'max-height': ($(window).height() - 280) + 'px' });
                }
            }
        }
    }
]);

appHelperModule.factory('guidGenerator', [function () {

    function guid() {
        function s4() {
            return Math.floor((1 + Math.random()) * 0x10000)
                .toString(16)
                .substring(1);
        }

        return s4() + s4() + '-' + s4() + '-' + s4() + '-' +
            s4() + '-' + s4() + s4() + s4();
    }

    return {
        generateNew: function () {
            return guid();
        }
    }
}]);

appHelperModule.directive('allowSingleCharacter', [function () {
    return {
        require: 'ngModel',
        link: function (scope, elem, attr, ngModelController) {
            var validValue;
            elem.on('keyup', function () {
                if (ngModelController.$viewValue.length < 2) {
                    validValue = ngModelController.$viewValue;
                } else {
                    ngModelController.$setViewValue(validValue);
                    ngModelController.$render();
                }
            });
        }
    }
}]);

appHelperModule.directive('surfImageSlider', [
    function () {
        return {
            restrict: 'EA',
            scope: {
                images: '=',
                selected: '=',
                onImageClick: '&',
                onNextImage: '&',
                onPreviousImage: '&'
            },
            templateUrl: './Templates/Lged/surfImageSlider.html',
            controller: ['$scope', function ($scope) {
                $scope.selected = $scope.selected ? $scope.selected : {};
                $scope.selected.Index = $scope.selected.Index || 0;

                $scope.next = function () {
                    if ($scope.selected.Index === $scope.images.length - 1) {
                        $scope.selected.Index = 0;
                        return;
                    }
                    ++$scope.selected.Index;
                    $scope.onNextImage();
                };

                $scope.previous = function () {
                    if ($scope.selected.Index === 0) {
                        $scope.selected.Index = $scope.images.length - 1;
                        return;
                    }
                    --$scope.selected.Index;
                    $scope.onPreviousImage();
                }

                $scope.onImageClicked = function () {
                    $scope.onImageClick();
                }
            }]
        }
    }
]);

