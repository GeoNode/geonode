mapModule.directive('mapLoadingIcon', [
   '$timeout',
    function ($timeout) {
        return {
            restrict: 'EA',
            template: '<div ng-if="isLoading" class="map-loading-icon donot-print"> <i class="fa fa-spinner fa-spin"></i> </div>',
            controller: [
                '$scope',
                function ($scope) {
                    $scope.isLoading = false;
                    var loadingCount = 0;

                    function layerLoadingStarted(olLayer) {
                        $timeout(function () {
                            if (olLayer) {
                                ++loadingCount;
                                $scope.isLoading = true;
                            }
                        });
                    }

                    function layerLoadingEnded(olLayer) {
                        $timeout(function () {
                            if (olLayer) {
                                --loadingCount;
                                $scope.isLoading = !!loadingCount;
                            }
                        });
                    }

                    jantrik.EventPool.register('layerLoadingStarted', function (olLayer) {
                        layerLoadingStarted(olLayer);
                    });
                    jantrik.EventPool.register('layerLoadingEnded', function (olLayer) {
                        layerLoadingEnded(olLayer);
                    });
                }]
        };
    }
]);