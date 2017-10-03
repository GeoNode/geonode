appHelperModule.directive('visualizationLegend', ['mapTools',
    function (mapTools) {
        return {
            restrict: 'EA',
            templateUrl: '/static/Templates/visualizationLegend.html',
            controller: ['$scope', function ($scope) {
                    $scope.activeLayerTool = mapTools.activeLayer;
                    
                    $scope.getSelectedAttributeName = function () {
                        var visualizationSettings = $scope.activeLayerTool.getActiveLayer().VisualizationSettings;
                        if (!visualizationSettings) return "";

                        var attribute = _.findWhere($scope.activeLayerTool.getActiveLayer().getAttributeDefinition(), { Id: visualizationSettings.attributeId });
                        if (!attribute) return "";

                        return attribute.Name;
                    }
                    
                    $scope.canRenderLegend = function () {
                        if ($scope.activeLayerTool) {
                            var activeLayer = $scope.activeLayerTool.getActiveLayer();
                            return activeLayer.VisualizationSettings && activeLayer.getFeatureType() != 'raster'
                                && activeLayer.VisualizationSettings.name == 'Choropleth' && activeLayer.IsVisible;
                        } else {
                            return false;
                        }
                    }
                }
            ]
        };
    }
]);
