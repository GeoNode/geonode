appHelperModule.directive('removeFocus', [
    function () {
        return {
            restrict: 'A',
            priority: -1,
            link: function (scope, elem) {
                elem.bind("click", function () {
                    elem.blur();
                });
            }
        };
    }
]);