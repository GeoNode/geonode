appModule.controller('layerPropertiesCtrl', ['$timeout', '$scope', '$http', '$filter', '$modalInstance', 'data', 'inputData', 'settingsData', 'layer',
    function ($timeout, $scope, $http, $filter, $modalInstance, data, inputData, settingsData, layer) {
        $scope.settingsData = settingsData;
        $scope.inputData = inputData;
        $scope.classifierBinder = { classType: undefined, colorPaletteGenerator: undefined }
        $scope.propertiesData = { isDirty: false };
        $scope.attributeDefs = data.fields;
        $scope.isReadonly = !layer.isWritable();
        $scope.nodeData = {};
        $scope.tabs = [{}, {}, {}, {}, {}];
        $scope.showSelectStyle = false;

        $timeout(function () {
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
            zoomlevel: layer.getZoomLevel()
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

        $scope.cancel = function () {
            $modalInstance.dismiss('cancel');
        };

        $scope.save = function () {
            if ($scope.nodeData.invalidField() || !$scope.nodeData.layer.name) {
                return;
            }
            $modalInstance.close({
                updatedNode: $scope.nodeData,
                fieldChanged: $scope.propertiesData.isDirty,
                classifierDefinitions: $scope.classifierBinder.classType.getSettings($scope.classifierBinder.colorPaletteGenerator),
                propertiesChanged: featurePropertiesDirty()
            });
        };
    }]);
