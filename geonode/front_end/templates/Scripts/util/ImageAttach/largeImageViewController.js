appModule.controller('largeImageViewController', [
    '$scope', 'surfToastr', 'featureService', 'isReadonly', '$modalInstance', function ($scope, surfToastr, featureService, isReadonly, $modalInstance) {

        $scope.isReadonly = isReadonly;
        $scope.next = function () {
            if ($scope.selectedIndex === $scope.images.length - 1) {
                $scope.selectedIndex = 0;
                return;
            }
            ++$scope.selectedIndex;
            $scope.currentImage = $scope.images[$scope.selectedIndex];
        };

        $scope.previous = function () {
            if ($scope.selectedIndex === 0) {
                $scope.selectedIndex = $scope.images.length - 1;
                return;
            }
            --$scope.selectedIndex;
            $scope.currentImage = $scope.images[$scope.selectedIndex];
        }

        $scope.deleteImage = function () {
            dialogBox.confirm({
                title: appMessages.confirm.confirmHeader,
                text: appMessages.confirm.deleteItem,
                action: function () {
                    var activeImage = _.findWhere($scope.getImages(), { active: true });

                    featureService.removeImageFromActiveFeature(activeImage).success(function () {
                        if ($scope.getImages().length === 0) {
                            $scope.$close();
                        }
                    });
                }
            });
        }
        $scope.downloadFile = function () {
            var activeImage = _.findWhere($scope.getImages(), { active: true });
            var dlpath = activeImage.link;
            $scope.toJSON = '';
            $scope.toJSON = angular.toJson($scope.data);
            var downloadLink = angular.element('<a></a>');
            downloadLink.attr('href', dlpath);
            downloadLink.attr('download', activeImage.oname);
            downloadLink[0].click();
        }

        $scope.close = function () {
            $modalInstance.close();
        }
    }
]);
