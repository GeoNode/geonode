mapModule
    .directive('zoomToMaxExtentButton', zoomToMaxExtentButton);
zoomToMaxExtentButton.$inject = ['mapTools'];

function zoomToMaxExtentButton(mapTools) {
    return {
        restrict: 'EA',
        scope: {},
        templateUrl: '/static/Templates/Tools/Map/zoomToMaxExtentButton.html',
        controller: [
            '$scope',
            function($scope) {
                angular.extend($scope, mapTools.zoomToMaxExtentTool);
            }
        ]
    };
}