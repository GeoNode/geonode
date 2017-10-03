appModule.controller('selectEpsgCodeController', [
    '$scope', 'epsgCodes', '$modalInstance', 'onSelect', 'fileId', 'fileName', 'epsgService',
    function ($scope, epsgCodes, $modalInstance, onSelect, fileId, fileName, epsgService) {
        $scope.isProcessing = false;
        $scope.epsgCodes = epsgCodes;
        $scope.data = {};
        $scope.closeModal = function () {
            $modalInstance.close(undefined);
        };

        $scope.selectEpsg = function (codeItem) {
            $scope.data.epsg = codeItem.code;
        };

        $scope.isEpsgKnown = function () {
            return epsgService.isEpsgKnown($scope.data.epsg);
        };

        $scope.submit = function () {
            $scope.isProcessing = true;
            if ($scope.isEpsgKnown()) {
                onSelect(fileId, fileName, $scope.data.epsg).success(function (data) {
                    $scope.isProcessing = false;
                    $modalInstance.close(data);
                }).error(function () {
                    $scope.isProcessing = false;
                    $modalInstance.close(undefined);
                });
            } else {
                $modalInstance.close(undefined);
            }
        };
    }
]);