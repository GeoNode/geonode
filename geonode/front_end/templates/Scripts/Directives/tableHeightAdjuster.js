angular.module('table.heightAdjuster', [])
    .directive('tableHeightAdjuster', ['$window',function ($window) {
    return {
        restrict: 'AC',
        link: function (scope, elem, attr, controller) {
            resizeTable();
            $window.onresize = function () {
                resizeTable();
            }
            function resizeTable() {
                var height = $window.innerHeight;
                angular.element(elem).css('max-height', (height - 413));
            }
        }
    }
}]);
