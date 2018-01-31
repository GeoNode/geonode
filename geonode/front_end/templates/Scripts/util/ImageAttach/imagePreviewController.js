appModule.controller('imagePreviewController', [
    '$scope', '$rootScope', '$modal', 'featureService', function ($scope, $rootScope, $modal, featureService) {

        $scope.getImages = function () {
            return featureService.getActive() && featureService.getActive().getImages();
        };

        $scope.getFeature = function () {
            return featureService.getActive();
        };

        $scope.hasFeature = function () {
            return featureService.hasActive();
        };

        $scope.isReadonly = function () {
            if (featureService.hasActive()) {
                return !featureService.getActive().layer.isWritable();
            }
            return false;
        }

        $scope.isLargeImageViewOn = false;

        $scope.showLargeImage = function () {
            $scope.isLargeImageViewOn = true;
            $modal.open({
                templateUrl: '/static/Templates/Carousel.html',
                controller: 'largeImageViewController',
                scope: $scope,
                backdrop: 'static',
                windowClass: 'image-previewer-dialog',
                resolve: {
                    isReadonly: function() {
                        return $scope.isReadonly();
                    }
                }
            }).result.finally(function () {
                $scope.isLargeImageViewOn = false;
            });
        };
        $scope.openAttachModal = function () {
            var feature = featureService.getActive();
            $modal.open({
                templateUrl: '/static/Templates/AttachFileDialog.html',
                controller: 'FileAttachController',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    feature: function () {
                        return feature;
                    }
                }
            });
        };

        $scope.openImageAttachModal = function () {
            var feature = featureService.getActive();
            $modal.open({
                templateUrl: '/static/Templates/AttachImageDialog.html',
                controller: 'ImageAttachController',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    feature: function () {
                        return feature;
                    }
                }
            });
        };
    }
]);
