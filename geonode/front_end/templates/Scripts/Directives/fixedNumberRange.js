appHelperModule.directive('fixedNumberRange', [
    function () {
        return {
            require: 'ngModel',
            link: function (scope, element, attrs, ngModelController) {
                element.on('keyup', function () {
                    var maxVal = parseFloat(attrs['max']);
                    var minVal = parseFloat(attrs['min']);
                    var currentVal = parseFloat(element.val());
                    if (isNaN(element.val()) && element.val() != "") {
                        ngModelController.$setViewValue(minVal);
                        ngModelController.$render();
                    }
                    if (currentVal > maxVal) {
                        ngModelController.$setViewValue(maxVal);
                        ngModelController.$render();
                    } else if (currentVal < minVal) {
                        ngModelController.$setViewValue(minVal);
                        ngModelController.$render();
                    }
                });

                element.on('blur', function () {
                    if (isNaN(element.val()) || element.val() == "") {
                        var minVal = parseFloat(attrs['min']);
                        ngModelController.$setViewValue(minVal);
                        ngModelController.$render();
                    }
                });
            }
        };
    }
]);