mapModule
    .directive('setMarker', setMarker);
setMarker.$inject = ['mapTools'];

function setMarker(mapTools) {
    return {
        restrict: 'EA',
        scope: {},
        templateUrl: '/static/Templates/Tools/Map/setMarkerButton.html',
        controller: [
            '$scope',
            function($scope) {
                angular.extend($scope, mapTools.setMarkerTool);
            }
        ]
    };
}