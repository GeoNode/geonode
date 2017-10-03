appModule.controller('addBlankLayerCtrl', ['$scope', '$modalInstance', function ($scope, $modalInstance) {
    $scope.layer = {};
    $scope.layerTypes = ["polygon", "polyline", "point"];

    $scope.cancel = function () {
        $modalInstance.dismiss('cancel');
    };

    $scope.save = function () {
        $modalInstance.close($scope.layer);
    };
}]);
