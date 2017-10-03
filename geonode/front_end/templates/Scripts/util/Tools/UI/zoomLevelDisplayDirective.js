mapModule.directive('zoomLevelDisplay', [
    'mapTools', '$timeout',
    function (mapTools, $timeout) {
        return {
            restrict: 'EA',
            scope: {

            },
            template: '<div class="zoom-level-display donot-print">{{zoom}}<div>',
            controller: [
                '$scope',
                function ($scope) {
                    $scope.zoom = mapTools.zoomTracker.zoom;

                    mapTools.zoomTracker.events.register('changed', function () {
                        $timeout(function() {
                            $scope.zoom = mapTools.zoomTracker.zoom;
                        });
                    });
                }
            ]
        };
    }
]);