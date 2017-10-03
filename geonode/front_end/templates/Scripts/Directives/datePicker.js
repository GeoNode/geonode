appHelperModule.directive('datePicker', [
    function () {
        return {
            restrict: 'A',
            require: 'ngModel',
            link: function (scope, element, attrs, ngModelCtrl) {
                element.datepicker({
                    showButtonPanel: true,
                    beforeShow: function (input) {
                        setTimeout(function () {
                            var buttonPane = $(input)
                                .datepicker("widget")
                                .find(".ui-datepicker-buttonpane");

                            buttonPane.empty();

                            $("<button>", {
                                text: "Clear",
                                click: function () {
                                    $.datepicker._clearDate(input);
                                }
                            }).appendTo(buttonPane).addClass("ui-datepicker-clear ui-state-default ui-priority-primary ui-corner-all");
                        }, 1);
                    },
                    dateFormat: 'yy-mm-dd',
                    onSelect: function (date) {
                        scope.$apply(function () {
                            ngModelCtrl.$setViewValue(date);
                        });
                    }
                });
            }
        };
    }
]);