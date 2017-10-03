mapModule.directive('featureEditButtons', [
    'interactionHandler', 'mapModes', 'mapTools',
    function (interactionHandler, mapModes, mapTools) {
        return {
            restrict: 'EA',
            scope: {
            },
            templateUrl: '/static/Templates/Tools/Layer/featureEditButtons.html',
            controller: [
                '$scope',
                function ($scope) {
                    var _activeLayer;
                    
                    $scope.action = {
                        toAddShapeMode: function () {
                            interactionHandler.setMode(mapModes.addShape);
                        },
                        toEditShapeMode: function () {
                            interactionHandler.setMode(mapModes.editShape);
                        },
                        toDeleteShapeMode: function () {
                            interactionHandler.setMode(mapModes.deleteShape);
                        }
                    };

                    $scope.active = {
                        editFeature: function () {
                            return interactionHandler.getMode() == mapModes.editShape;
                        },
                        addFeature: function () {
                            return interactionHandler.getMode() == mapModes.addShape;
                        },
                        deleteFeature: function () {
                            return interactionHandler.getMode() == mapModes.deleteShape;
                        }
                    };

                    function setActiveLayer(activeLayer) {
                        if (!activeLayer) {
                            return;
                        }
                        _activeLayer = activeLayer;
                    }
                    
                    mapTools.activeLayer.events.register('changed', function (newActiveLayer) {
                        setActiveLayer(newActiveLayer);
                    });

                    setActiveLayer(mapTools.activeLayer.getActiveLayer());

                    $scope.show = true;
                    mapTools.geoLocation.events.register('activated', function () {
                        $scope.show = false;
                    }).register('deactivated', function() {
                        $scope.show = true;
                    });
                }
            ]
        };
    }
]);