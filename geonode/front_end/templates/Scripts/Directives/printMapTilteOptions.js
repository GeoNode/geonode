appHelperModule.directive('printMapTitleOptions', [
    function () {
        return {
            templateUrl: 'static/Templates/printMapTitleOptions.html',
            scope: {
                options: '=printMapTitleOptions'
            },
            controller: ['$scope', function ($scope) {
                $scope.alignments = ['left', 'center', 'right'];
            }]
        };
    }
]);

