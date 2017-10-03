appHelperModule.directive('stylePreview', [
    'featureTypes', 'strokeDashstyles',
    function (featureTypes, strokeDashstyles) {
        return {
            templateUrl: './Templates/stylePreview.html',
            restrict: 'AE',
            replace: true,
            scope: {
                styleHash: '=',
                featureType: '=',
                previewSize: '=?'
            },
            controller: [
                '$scope', 'guidGenerator',
                function ($scope, guidGenerator) {

                    $scope.uniqueId = guidGenerator.generateNew();

                    var _styleHash = $scope.styleHash;
                   
                    $scope.previewSize = $scope.previewSize || {};
                    var _size = $scope.previewSize;
                    _size.width = _size.width || 50;
                    _size.height = _size.height || 50;

                    if (_size.width != _size.height) {
                        _size.width = Math.min(_size.width, _size.height);
                        _size.height = _size.width;
                    }

                    $scope.getDashArray = function () {
                        return strokeDashstyles.getDashedArray(_styleHash);
                    };

                    $scope.isPoint = $scope.featureType == featureTypes.point;
                    $scope.isPolyline = $scope.featureType == featureTypes.polyline;
                    $scope.isPolygon = $scope.featureType == featureTypes.polygon;

                    if ($scope.isPoint) {
                        $scope.$watch('styleHash.pointRadius', function () {
                            $scope.r = _styleHash.pointRadius;
                            $scope.halfR = $scope.r / 2;
                            $scope.thirdR = $scope.r * 0.3; // not third actually
                            $scope.fifthR = $scope.r / 5;

                            $scope.left = (_size.width / 2) - _styleHash.pointRadius;
                            $scope.right = (_size.width / 2) + parseInt(_styleHash.pointRadius);
                            $scope.top = (_size.height / 2) - _styleHash.pointRadius;
                            $scope.bottom = (_size.height / 2) + parseInt(_styleHash.pointRadius);
                        });

                        $scope.$watch('previewSize.width', function () {
                            $scope.cx = _size.width / 2;
                        });

                        $scope.$watch('previewSize.height', function () {
                            $scope.cy = _size.height / 2;
                        });
                    }

                    $scope.style = "";

                    $scope.getFill = function (style) {
                        if (style.fillPattern) {
                            return "url(#" + style.fillPattern + $scope.uniqueId + ")";
                        }
                        return style.fillColor;
                    }
                }
            ]
        };
    }
]);