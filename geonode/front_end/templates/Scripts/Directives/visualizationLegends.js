appHelperModule.directive('visualizationLegend', ['mapTools', 'utilityService',
    function (mapTools, utilityService) {
        return {
            restrict: 'EA',
            templateUrl: '/static/Templates/visualizationLegend.html',
            controller: ['$scope', function ($scope) {
                    $scope.activeLayerTool = mapTools.activeLayer;
                    
                    $scope.getSelectedAttributeName = function () {
                        var visualizationSettings = $scope.activeLayerTool.getActiveLayer().style.VisualizationSettings;
                        if (!visualizationSettings) return "";

                        var attribute = _.findWhere($scope.activeLayerTool.getActiveLayer().getAttributeDefinition(), { Id: visualizationSettings.attributeId });
                        if (!attribute) return "";

                        return attribute.Name;
                    };
                    
                    $scope.canRenderLegend = function () {
                        if ($scope.activeLayerTool) {
                            var activeLayer = $scope.activeLayerTool.getActiveLayer();
                            return activeLayer.Style && activeLayer.Style.VisualizationSettings && activeLayer.getFeatureType() != 'raster'
                                && isLegendAllowed(activeLayer.Style.VisualizationSettings) && activeLayer.IsVisible;
                        } else {
                            return false;
                        }
                    };

                    $scope.visName = '';
                    function isLegendAllowed(config){
                        $scope.visName = config.name;
                        $scope.visConfig = config;
                        return config.name === 'Chart';
                    }

                    $scope.legendItems = [];
                    $scope.chartSelectedAttributes = function(){
                        var selectedAttributes = utilityService.getChartSelectedAttributes($scope.visConfig);
                        return _.map(selectedAttributes, function(item){ 
                            return { name: item.numericAttribute.Name, color: item.attributeColor };
                        });
                        
                    };
                }
            ]
        };
    }
]);
