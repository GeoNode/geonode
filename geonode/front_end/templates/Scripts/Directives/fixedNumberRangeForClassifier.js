appHelperModule.directive('fixedNumberRangeForClassifier', [
    function () {
        return {
            require: 'ngModel',
            link: function (scope, element, attrs, ngModelController) {

                element.on('blur', function () {
                    applyChanges();
                });

                function applyChanges() {
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
                }
            }
        };
    }
]);