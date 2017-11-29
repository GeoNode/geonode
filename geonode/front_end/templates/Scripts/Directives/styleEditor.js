appHelperModule.directive('styleLabel', [
    'featureTypes',
    function (featureTypes) {
        return {
            restrict: 'EA',
            templateUrl: 'static/Templates/styleLabel.html',
            scope: {
                featureType: '='
            },
            controller: [
                '$scope',
                function ($scope) {
                    $scope.isPoint = $scope.featureType == featureTypes.point;
                    $scope.isPolyline = $scope.featureType == featureTypes.polyline;
                    $scope.isPolygon = $scope.featureType == featureTypes.polygon;
                }
            ]
        };
    }]);

appHelperModule.directive('styleEditor', [
    'strokeDashstyles', 'pointGraphics', 'featureTypes', 'pointGraphicNames', 'polygonFillPatterns', 'pointTextGraphics',
    function (strokeDashstyles, pointGraphics, featureTypes, pointGraphicNames, polygonFillPatterns, pointTextGraphics) {
        return {
            restrict: 'E',
            scope: {
                styleHash: '=',
                featureType: '='
            },
            templateUrl: 'static/Templates/styleEditor.html',
            controller: [
                '$scope',
                function ($scope) {
                    var _model = {
                        transparency: 100 - ($scope.styleHash.fillOpacity * 100),
                        pointType: $scope.styleHash.externalGraphic || $scope.styleHash.graphicName || $scope.styleHash.textGraphicName
                    };
                    $scope.model = _model;
                    $scope.styleHash['cursor'] = 'pointer';
                    $scope.fillPatterns = polygonFillPatterns.allPatterns;

                    $scope.graphicIconClass = pointGraphicNames.graphicIconClass;
                    $scope.pointGraphicNames = pointGraphicNames.allGraphics;

                    $scope.textGraphicIconClasses = pointTextGraphics.textGraphicIconClasses;
                    $scope.pointTextGraphicNames = pointTextGraphics.allTextGraphics;

                    $scope.strokeDashstyles = strokeDashstyles;
                    $scope.pointGraphics = pointGraphics;

                    $scope.isPoint = $scope.featureType == featureTypes.point;
                    $scope.isPolyline = $scope.featureType == featureTypes.polyline;
                    $scope.isPolygon = $scope.featureType == featureTypes.polygon;

                    $scope.transparencyChanged = function () {
                        $scope.styleHash.fillOpacity = (100 - $scope.model.transparency) / 100;
                    };

                    $scope.$watch('model.transparency', function () {
                        $scope.styleHash.fillOpacity = (100 - $scope.model.transparency) / 100;
                    });
                    var ftime = true;
                    var _mode = "text";
                    $scope.$watch('model.pointType', function () {
                        $scope.styleHash.textFontAwesome = false;
                        var mode = "";
                        if (pointGraphicNames.isValidGraphic(_model.pointType)) {
                            $scope.styleHash.graphicName = _model.pointType;
                            $scope.styleHash.externalGraphic = null;
                            $scope.styleHash.textGraphicName = null;
                        } else if (pointTextGraphics.isValidTextGraphic(_model.pointType)) {
                            mode = "text";
                            $scope.styleHash.textGraphicName = _model.pointType;
                            $scope.styleHash.graphicName = null;
                            $scope.styleHash.externalGraphic = null;
                        } else if (pointTextGraphics.isValidFontAwesomeGraphic(_model.pointType)) {
                            mode = "graphic";
                            $scope.styleHash.textFontAwesome = true;
                            $scope.styleHash.textGraphicName = _model.pointType;
                            $scope.styleHash.graphicName = null;
                            $scope.styleHash.externalGraphic = null;
                        }
                        else {
                            $scope.styleHash.externalGraphic = _model.pointType;
                            $scope.styleHash.textGraphicName = null;
                            $scope.styleHash.graphicName = null;
                        }
                        if (mode !== _mode && !ftime)
                            $scope.styleHash.text = "";
                        ftime = false;
                        _mode = mode;
                 
                    });
    }
]
};
}
]);
