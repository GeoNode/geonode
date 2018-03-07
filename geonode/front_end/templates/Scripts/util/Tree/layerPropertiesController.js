appModule.controller('layerPropertiesCtrl', ['$timeout', '$scope', '$http', '$filter', '$modalInstance', 'data', 'inputData', 'settingsData', 'layer', 'LayerService',
    function($timeout, $scope, $http, $filter, $modalInstance, data, inputData, settingsData, layer, LayerService) {
        $scope.settingsData = settingsData;
        $scope.inputData = inputData;
        $scope.classifierBinder = { classType: undefined, colorPaletteGenerator: undefined };
        $scope.propertiesData = { isDirty: false };
        $scope.attributeDefs = data.fields;
        $scope.isReadonly = !layer.isWritable();
        $scope.nodeData = {};
        $scope.tabs = [{}, {}, {}, {}, {}];
        $scope.showSelectStyle = false;

        $scope.visualizationSettings = { selected: layer.Style.VisualizationSettings };

        $timeout(function() {
            $scope.tabs[data.selectedTabIndex].active = true;
        });

        $scope.nodeData.layer = {
            name: layer.getName(),
            shapeType: layer.getFeatureType(),
            dataSourceName: layer.getDataSourceName(),
            style: angular.copy(layer.getStyle()),
            id: layer.getId(),
            linearUnit: layer.linearUnit,
            attributeDefinitions: layer.getAttributeDefinition(),
            zoomlevel: layer.getZoomLevel(),
            //visualizationSettings: layer.visualizationSettings
        };

        $scope.nodeData.fields = data.fields;

        function featurePropertiesDirty() {
            var oldStyle = layer.getStyle();
            var newStyle = $scope.nodeData.layer.style;

            var styleChanged = false;
            for (var s in { 'default': 0, 'select': 1, 'labelConfig': 2 }) {
                for (var k in newStyle[s]) {
                    if (newStyle[s][k] != oldStyle[s][k]) {
                        styleChanged = true;
                    }
                }
            }

            return layer.getName() != $scope.nodeData.layer.name || layer.getZoomLevel() != $scope.nodeData.layer.zoomlevel || styleChanged;
        }

        $scope.cancel = function() {
            $modalInstance.dismiss('cancel');
        };

        function getLayerStyles() {
            LayerService.getStylesByLayer(layer.getName())
                .then(function(res) {
                    console.log(res);
                    $scope.Styles = res.results;
                    $scope.Styles.forEach(function(e){
                        if(e.id == $scope.nodeData.layer.style.id){
                            $scope.nodeData.selectedStyle = e;
                        }
                    });
                }, function() {

                });
        }
        (getLayerStyles)();
        $scope.onStyleChange = function() {
            if (!$scope.nodeData.selectedStyle || !$scope.nodeData.selectedStyle.hasOwnProperty('id'))
                return;
            LayerService.getStyle($scope.nodeData.selectedStyle.id)
            .then(function(res) {
                    $scope.nodeData.layer.style = res;

                    $scope.settingsData = $scope.nodeData.layer.style.classifierDefinitions || {};
                    $scope.classifierBinder = { classType: undefined, colorPaletteGenerator: undefined };
                }, function() {

                });
        };

        $scope.newStyle = function() {
            console.log(inputData, settingsData);
            angular.copy(LayerService.getNewStyle(), $scope.nodeData.layer.style);
            $scope.nodeData.selectedStyle = $scope.nodeData.layer.style;
            $scope.settingsData = {};
            $scope.classifierBinder = { classType: undefined, colorPaletteGenerator: undefined };
            $scope.Styles.push($scope.nodeData.layer.style);
        };

        $scope.save = function() {
            //if ($scope.nodeData.invalidField() || !$scope.nodeData.layer.name) {
            if (!$scope.nodeData.layer.name) {
                return;
            }
            layer.Style.VisualizationSettings = $scope.visualizationSettings.selected;
            $modalInstance.close({
                updatedNode: $scope.nodeData,
                fieldChanged: $scope.propertiesData.isDirty,
                classifierDefinitions: $scope.classifierBinder.classType.getSettings($scope.classifierBinder.colorPaletteGenerator),
                propertiesChanged: featurePropertiesDirty()
            });
        };
    }
]);