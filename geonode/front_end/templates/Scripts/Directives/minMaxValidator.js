appHelperModule.directive("minMaxValidator", ["$timeout", function ($timeout) {
    function updateModelValue(modelController, value) {
        $timeout(function () {
            modelController.$setViewValue(value);
            modelController.$render();
        });
    }
    return {
        restrict: "A",
        require: "ngModel",
        link: function (scope, elem, attr, ngModelController) {
            var minVal = parseFloat(attr["minval"]);
            var maxVal = parseFloat(attr["maxval"]);
            var defaultValue = parseFloat(attr["defaultval"]);

            scope.$watch(attr.ngModel, function (value, oldValue) {
                var number = parseFloat(value);
                if (!isNaN(number)) {
                    if (number < minVal || number > maxVal) {
                        updateModelValue(ngModelController, oldValue);
                    }
                }
            });

            elem.on("blur", function () {
                var number = parseFloat(ngModelController.$viewValue);
                if (isNaN(number)) {
                    updateModelValue(ngModelController, defaultValue);
                }
            });
        }
    };
}]);
