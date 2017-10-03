mapModule.directive('editToggleButton', [
    'interactionHandler', 'mapTools',
    function (interactionHandler, mapTools) {
        return {
            restrict: 'EA',
            scope: {},
            templateUrl: '/static/Templates/Tools/Map/editToggleButton.html',
            controller: [
                '$scope',
                function ($scope) {
                    function updateEnabledState() {
                        $scope.enabled = mapTools.activeLayer.getActiveLayer().isWritable()
                            && !mapTools.activeLayer.getActiveLayer().tools.selectFeature.isNull;
                    }

                    $scope.toggleMapEditable = function () {
                        interactionHandler.toggleEditable();
                    };

                    $scope.isEditing = function () {
                        return interactionHandler.isEditing();
                    };

                    mapTools.activeLayer.events.register('changed', updateEnabledState);
                    mapTools.activeLayer.events.register('updateEnableState', updateEnabledState);

                    updateEnabledState();
                }
            ]
        };
    }
]);
