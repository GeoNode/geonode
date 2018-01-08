mapModule.directive('baseMapSwitcher', [
    'mapTools',
    function (mapTools) {
        return {
            restrict: 'EA',
            scope: {},
            templateUrl: '/static/Templates/Tools/Map/baseMapSwitcher.html',
            controller: [
                '$scope',
                function ($scope) {
                    var baseMapTool = mapTools.baseMap;
                    $scope.baseMaps = baseMapTool.getAllBaseMaps();
                    $scope.baseMapGroups = _.groupBy($scope.baseMaps, function(item){ return item.groupName; });
                    $scope.model = {};

                    $scope.changed = function (basemap) {
                        $scope.model.selectedBaseMap = basemap;
                        baseMapTool.changeBaseLayer($scope.model.selectedBaseMap);
                    };

                    loadBaseMap();

                    if (!$scope.model.selectedBaseMap || !$scope.model.selectedBaseMap.title) {
                        baseMapTool.events
                            .register('set', loadBaseMap);
                    }
                    
                    function loadBaseMap() {
                        $scope.model.selectedBaseMap = baseMapTool.getBaseMap();
                    }
                }
            ]
        };
    }
]);