mapModule.directive('geoLocationToggleButton', [
    'mapTools',
    function (mapTools) {
        return {
            restrict: 'EA',
            scope: {},
            templateUrl: '/static/Templates/Tools/Map/geoLocationToggleButton.html',
            controller: [
                '$scope',
                function ($scope) {
                    var geoLocationTool = mapTools.geoLocation;
                    
                    $scope.autoCenterEnabled = geoLocationTool.isAutoCenterEnabled();

                    $scope.isTracking = function() {
                        return geoLocationTool.isActive();
                    };

                    $scope.toogleAutoCenterEnabled = function () {
                        geoLocationTool.setAutoCenterEnabled(!geoLocationTool.isAutoCenterEnabled());
                    };

                    $scope.toggleTracking = function () {
                        if (!geoLocationTool.isActive()) {
                            geoLocationTool.activate();
                        } else {
                            geoLocationTool.deactivate();
                        }
                    };
                }
            ]
        };
    }
]);