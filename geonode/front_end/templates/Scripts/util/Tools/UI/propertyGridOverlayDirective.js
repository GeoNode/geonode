appHelperModule.directive('propertyGridOverlay', [
    'mapTools',
    'attributeTypes',
    function (mapTools, attributeTypes) {
        return {
            replace: true,
            restrict: 'AE',
            templateUrl: '/static/Templates/Tools/Layer/propertyGridOverlay.html',
            scope: {
                isDraft: '=',
                options: '='
            },
            controller: ['$scope','mapAccessLevel',
                function ($scope, mapAccessLevel) {
                    var activeLayerTool = mapTools.activeLayer;
                    var attributeDisplayTool;
                    $scope.properties = [];
                    
                    $scope.canDisplayRow = function (property) {
                        if (mapAccessLevel.isPublic) {
                            return property.isPublished;
                        } else {
                            return true;
                        }
                    }

                    function createOverlay(surfFeature) {
                        $scope.properties = surfFeature.getAttributesWithType();
                    }

                    function registerToActiveLayer(activeLayer) {
                        attributeDisplayTool = activeLayer.tools.displayAttribute;
                        attributeDisplayTool.events.register('selected', createOverlay);
                    }

                    $scope.showUnit = function (property) {
                        return attributeTypes.hasUnit(property.type);
                    };

                    activeLayerTool.events.register('changed', function (newActiveLayer, oldActiveLayer) {
                        registerToActiveLayer(newActiveLayer);
                        oldActiveLayer.tools.displayAttribute.events.unRegister('selected', createOverlay);
                    });

                    registerToActiveLayer(activeLayerTool.getActiveLayer());
                }]
        };
    }
]);