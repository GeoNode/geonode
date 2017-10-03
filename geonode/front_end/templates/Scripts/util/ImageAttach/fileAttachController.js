appModule.controller('FileAttachController', ['$scope', 'FileUploader', 'feature', 'surfToastr', 'dirtyManager', 'urlResolver',
    function ($scope, FileUploader, feature, surfToastr, dirtyManager, urlResolver) {

        var fid = feature.getFid();
        var layerId = feature.layer.getId();
        var errorOccured = false;
        $scope.uploader = new FileUploader({
            url: urlResolver.resolveFeature('AttachImage', { fid: fid, layerId: layerId })
        });

        $scope.uploader.onSuccessItem = function (item, response) {
            feature.addImages([response.id]);
        };

        $scope.cancelAll = function () {
            errorOccured = true;
            $scope.uploader.cancelAll();
        }

        $scope.closeModal = function () {
            $scope.uploader.cancelAll();
            errorOccured = true;
            $scope.$close();
        };

        $scope.uploader.onErrorItem = function (fileItem, response, status, headers) {
            surfToastr.error(appMessages.toastr.imageUploadFailed(fileItem._file.name));
            errorOccured = true;
        };

        $scope.uploader.onCompleteAll = function () {
            $scope.$close();
            if (!errorOccured) {
                surfToastr.success(appMessages.toastr.filesAdded());
            }
            dirtyManager.setDirty(true);
        };
    }
]);
