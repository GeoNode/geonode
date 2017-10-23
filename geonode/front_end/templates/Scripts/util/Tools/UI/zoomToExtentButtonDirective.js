mapModule
    .directive('zoomToExtentButton', zoomToExtentButton);
zoomToExtentButton.$inject = ['mapTools'];

function zoomToExtentButton(mapTools) {
    return {
        restrict: 'EA',
        scope: {},
        templateUrl: '/static/Templates/Tools/Map/zoomToExtentButton.html',
        controller: [
            '$scope',
            function($scope) {
                angular.extend($scope, mapTools.zoomToExtentTool);
            }
        ]
    };
}