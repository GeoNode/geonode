mapModule
.directive('measurementButtons', measurementButtons);
measurementButtons.$inject = ['mapTools'];

function measurementButtons(mapTools) {
return {
    restrict: 'EA',
    scope: {},
    templateUrl: '/static/Templates/Tools/Map/measurementButtons.html',
    controller: [
        '$scope',
        function($scope) {
            angular.extend($scope, mapTools.measurementTool);
        }
    ]
};
}