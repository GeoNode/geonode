appHelperModule.directive('modalWindow', [function () {
    return {
        restrict: 'EAC',
        link: function (scope, element) {
            element.draggable({ handle: '.draggable-div, .modal-header, .modal-footer' });
        }
    }
}]);
