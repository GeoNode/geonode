appHelperModule.directive('colorCodeValidator', [
    function () {
        return {
            require: 'ngModel',
            restrict: 'A',
            link: function (scope, element, attr, ngModel) {
                ngModel.$parsers.unshift(function (value) {
                    if (value && value[0] != '#') {
                        value = '#' + value;
                    }
                    //http://stackoverflow.com/a/8027444/887149
                    var valid = /(^#[0-9A-F]{6}$)|(^#[0-9A-F]{3}$)/i.test(value);

                    ngModel.$setValidity('colorCode', valid);
                    if (!valid) {
                        value = ngModel.$modelValue;
                    }

                    return value;
                });
            }
        }
    }
])