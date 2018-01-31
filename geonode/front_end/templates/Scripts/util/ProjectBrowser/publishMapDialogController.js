appModule.controller('publishMapDialogController', [
    '$scope', 'selectedMap', '$modalInstance', 'mapRepository', 'urlResolver', 'mapService',
    function ($scope, selectedMap, $modalInstance, mapRepository, urlResolver, mapService) {

        $scope.previewSize = {
            width: 800,
            height: 600
        };

        mapRepository.getMapSummary(selectedMap.ProjectId).success(function (mapSummary) {
            $scope.mapSummary = mapSummary;
            $scope.mapSummary.PublicUrl = urlResolver.resolveMapAbsolute('Public', mapSummary.PublicId);
            $scope.mapSummary.EmbeddedUrl = urlResolver.resolveMapAbsolute('Embedded', mapSummary.PublicId);
        });

        $scope.publish = function () {
            saveAndExit(true);
        };

        $scope.unPublish = function () {
            saveAndExit(false);
        };

        function saveAndExit(isPublic) {
            var currentExtent = mapService.getMapExtent();
            $scope.mapSummary.IsPublic = isPublic;
            $scope.mapSummary.InitialExtent = { XMin: currentExtent[0], YMin: currentExtent[1], XMax: currentExtent[2], YMax: currentExtent[3] };
            mapRepository.saveMapSummary($scope.mapSummary).success(function () {
                selectedMap.IsPublic = $scope.mapSummary.IsPublic;
            });
            $scope.closeModal();
        };

        $scope.closeModal = function () {
            $modalInstance.close();
        };

        $scope.embedCode = function () {
            if (!$scope.mapSummary) {
                return '';
            }

            return '<iframe src="' + $scope.mapSummary.EmbeddedUrl + '" allowtransparency="true" frameborder="0" scrolling="no" allowfullscreen mozallowfullscreen webkitallowfullscreen oallowfullscreen msallowfullscreen width="' + $scope.previewSize.width + '" height="' + $scope.previewSize.height + '"></iframe>';
        };
    }
]);