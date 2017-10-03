mapModule.directive('layerLegends', [
    'mapService',
    function (mapService) {
        return {
            restrict: 'EA',
            scope: {},
            templateUrl: './Templates/Tools/Map/layerLegends.html',
            controller: [
                '$scope',
                function ($scope) {
                    $scope.expanded = true;

                    $scope.getLayers = function() {
                        return mapService.getLayers();
                    };
                }
            ]
        };
    }
]);