mapModule.directive('navigationHistoryButtons', [
    'mapTools',
    function (mapTools) {
        return {
            restrict: 'EA',
            scope: {},
            templateUrl: '/static/Templates/Tools/Map/navigationHistoryButtons.html',
            controller: [
                '$scope',
                function ($scope) {
                    angular.extend($scope, mapTools.navigationHistory);
                }
            ]
        };
    }
]);