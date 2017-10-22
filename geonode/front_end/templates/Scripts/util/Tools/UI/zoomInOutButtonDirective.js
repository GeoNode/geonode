mapModule.directive('zoomInOutButtons', [
    'mapTools',
    function (mapTools) {
        return {
            restrict: 'EA',
            scope: {},
            templateUrl: '/static/Templates/Tools/Map/zoomInOutButtons.html',
            controller: [
                '$scope',
                function ($scope) {
                    angular.extend($scope, mapTools.zoomInOutTool);
                }
            ]
        };
    }
]);