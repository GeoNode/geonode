angular.module('colorPalette',[]).directive("stiPltPkr", ["$document", function ($document) {
    return {
        restrict: "E",
        require: "ngModel",
        scope: {
            options: '=stiPkrOptions',
            choice: '=ngModel'
        },
        template:
            "<div class='palette-picker-container' ng-click='togglePicker()'>" + '<p class="choose">Choose color palette</p>' +
                "<div>" +
                    "<ul class='palette-choice-list'>" +
                        
                        "<li ng-repeat='opt in options track by $index' class='palette-choice' ng-click='choosePalette($event, opt)' ng-show='pickerVisible || isSelected(opt)'>" +
                            "<span ng-repeat='(name, val) in opt' class='color-preview' title='{{name}}' style='background-color:{{val}};'></span>" +
                        "</li>" +
                    "</ul>" +
                "</div>" +
                "<span class='down-arrow'>&#x25BE;</span>" +
            "</div>",
        link: function (scope, element, attributes) {

            scope.togglePicker = function () {
                scope.pickerVisible = !scope.pickerVisible;
            };

            scope.choosePalette = function ($event, item) {
                $event.stopPropagation();
                scope.togglePicker();
                scope.choice = item;
            };

            scope.isSelected = function (opt) {
                return opt == scope.choice;
            };

            scope.isOptionSelected = function () {
                return !(!scope.choice);
            };
            scope.clearSelection = function ($event) {
                scope.choice = undefined;
            };
        }
    };
}]);