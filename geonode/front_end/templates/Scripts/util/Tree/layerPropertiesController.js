appModule.controller('layerPropertiesCtrl', ['$timeout', '$scope', '$http', '$filter', '$modalInstance', 'data', 'inputData', 'settingsData', 'layer', 'LayerService', 'surfToastr',
    function($timeout, $scope, $http, $filter, $modalInstance, data, inputData, settingsData, layer, LayerService, surfToastr) {
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

        function initNodeData() {

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
        }

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
                    $scope.Styles = res;
                    $scope.settingsData = $scope.nodeData.layer.style.classifierDefinitions || {};
                    $scope.classifierBinder = { classType: undefined, colorPaletteGenerator: undefined };
                    $scope.visualizationSettings = { selected: $scope.nodeData.layer.style.visualizationSettings };
                    $scope.nodeData.selectedStyle = $scope.Styles.find(function(e) {
                        return e.id == $scope.nodeData.layer.style.id;
                    });
                }, function() {

                });
        }
        initNodeData();
        (getLayerStyles)();
        $scope.onStyleChange = function() {
            if (!$scope.nodeData.selectedStyle || !$scope.nodeData.selectedStyle.hasOwnProperty('id'))
                return;
            LayerService.getStyle($scope.nodeData.selectedStyle.id)
                .then(function(res) {
                    $scope.nodeData.layer.style = res;
                    
                    $scope.settingsData = $scope.nodeData.layer.style.classifierDefinitions || {};
                    $scope.classifierBinder = { classType: undefined, colorPaletteGenerator: undefined };
                    $scope.visualizationSettings = { selected: $scope.nodeData.layer.style.visualizationSettings };

                    layer.setStyle({
                        id: $scope.nodeData.selectedStyle.id,
                        Name: $scope.nodeData.selectedStyle.style.name,
                        Title: $scope.nodeData.selectedStyle.title
                    });
                    layer.refresh();
                }, function() {

                });
        };

        $scope.newStyle = function() {
            angular.copy(LayerService.getNewStyle(), $scope.nodeData.layer.style);
            $scope.nodeData.selectedStyle = $scope.nodeData.layer.style;
            $scope.settingsData = {};
            $scope.classifierBinder = { classType: undefined, colorPaletteGenerator: undefined };
            $scope.Styles.push($scope.nodeData.selectedStyle);
            $scope.visualizationSettings = { selected: undefined };
        };

        $scope.deleteStyle = function() {
            if (!$scope.nodeData.selectedStyle) {
                surfToastr.warning('Please select a style first', 'No Style');
                return;
            }
            var res = confirm("Are you suer you want to delete " + $scope.nodeData.selectedStyle.title);
            if (!res) {
                return;
            }
            LayerService.deleteStyle($scope.nodeData.selectedStyle.id)
                .then(function() {
                    surfToastr.success('Style deleted successfully', 'Style Deletion Success');
                    var index = $scope.Styles.findIndex(function(e) {
                        return e.id == $scope.nodeData.selectedStyle.id;
                    });
                    $scope.Styles.splice(index, 1);
                    $scope.nodeData.selectedStyle = $scope.Styles[0];
                    $scope.onStyleChange();
                }, function(res) {
                    surfToastr.error(res.error, 'Style Deletion Failed');
                });
        };

        $scope.save = function() {
            //if ($scope.nodeData.invalidField() || !$scope.nodeData.layer.name) {
            if (!$scope.nodeData.layer.name) {
                return;
            }
            $scope.nodeData.layer.style.visualizationSettings = $scope.visualizationSettings.selected;
            $modalInstance.close({
                updatedNode: $scope.nodeData,
                fieldChanged: $scope.propertiesData.isDirty,
                classifierDefinitions: $scope.classifierBinder.classType.getSettings($scope.classifierBinder.colorPaletteGenerator),
                propertiesChanged: featurePropertiesDirty()
            });
        };
    }
]);