mapModule
    .directive('zoomInOutButtons', zoomInOutButtons);
zoomInOutButtons.$inject = ['mapTools'];

function zoomInOutButtons(mapTools) {
    return {
        restrict: 'EA',
        scope: {},
        templateUrl: '/static/Templates/Tools/Map/zoomInOutButtons.html',
        controller: [
            '$scope',
            function($scope) {
                angular.extend($scope, mapTools.zoomInOutTool);
            }
        ]
    };
}