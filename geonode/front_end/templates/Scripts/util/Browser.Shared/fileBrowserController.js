appModule.controller('fileBrowserController', ['$scope', 'userProfileService',
    function ($scope, userProfileService) {
        $scope.viewOptions = ['List view', 'Grid view'];
        $scope.fileTypes = ['All', 'Polygon', 'Polyline', 'Point', 'CSV', 'GeoTIFF'];
        $scope.fileType = { type: $scope.fileTypes[0] };
        if ($scope.type.isProject) {
            $scope.viewOption = { currentView: $scope.viewOptions[1] };
        } else {
            $scope.viewOption = { currentView: userProfileService.getSetting('DataBrowserView') || $scope.viewOptions[0] };
            $scope.$watch('viewOption.currentView', function () {
                userProfileService.saveSetting('DataBrowserView', $scope.viewOption.currentView);
            });
        }
    }]);
