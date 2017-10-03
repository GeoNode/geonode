angular.module('checkboxAll',[]).directive("checkboxAll", function () {
    
    return function (scope, iElement, iAttrs) {
        var parts = iAttrs.checkboxAll.split('-');
        iElement.attr('type', 'checkbox');
        iElement.bind('change', function (evt) {
            scope.$apply(function () {
                var setValue = iElement.prop('checked');
                angular.forEach(scope.$eval(parts[0]), function (v) {
                    v[parts[1]] = setValue;
                });
            });
        });
        scope.$watch(parts[0], function (newVal) {
            var hasTrue = false, hasFalse = false;
            angular.forEach(newVal, function (v) {
                if (v[parts[1]]) {
                    hasTrue = true;
                } else {
                    hasFalse = true;
                }
            });
            if (hasTrue && hasFalse) {
                iElement.attr('checked', false);
                iElement.prop('indeterminate', true);
            } else {
                iElement.attr('checked', hasTrue);
                iElement.prop('indeterminate', false);
            }
        }, true);
    };
    
});