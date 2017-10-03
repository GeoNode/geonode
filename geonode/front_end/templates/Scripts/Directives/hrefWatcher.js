appHelperModule.directive('hrefWatcher', [
    function () {
        return {
            restrict: 'A',
            replace: true,
            template: '<div><span ng-if="!isUrl()">{{hrefWatcher}}</span>' +
                '<div ng-if="isUrl()"><a target="_blank" ng-href="{{hrefWatcher}}">{{hrefWatcher}}<a></div></div>',
            scope: {
                hrefWatcher: '='
            },
            controller: [
                '$scope', function ($scope) {
                    var urlValidator = new RegExp(/(http|ftp|https):\/\/[\w-]+(\.[\w-]+)+([\w.,@?^=%&amp;:\/~+#-]*[\w@?^=%&amp;\/~+#-])?/);
                    $scope.isUrl = function () {
                        return urlValidator.test($scope.hrefWatcher);
                    }
                }
            ]
        };
    }
]);
