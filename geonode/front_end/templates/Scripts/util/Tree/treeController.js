appModule.controller('treeController', ['$scope', '$window', '$http', '$rootScope', '$modal', '$timeout', 'mapRepository', 'mapService', 'layerService', 'mapTools',
    function($scope, $window, $http, $rootScope, $modal, $timeout, mapRepository, mapService, layerService, mapTools) {
        $scope.mapService = mapService;
        var activeLayerTool = mapTools.activeLayer || {
            hasActiveLayer: function() { return false; }
        };
        $scope.activeLayerTool = activeLayerTool;
        $scope.sortableOptions = {
            stop: function() {
                var sortOrderMappings = [];

                angular.forEach(mapService.sortableLayers, function(surfLayer, order) {
                    surfLayer.setSortOrder(parseInt(order) + 1);
                    sortOrderMappings.push({ LayerId: surfLayer.getId(), SortOrder: surfLayer.getSortOrder() });
                });
                mapService.updateLayerViewOrders();
                mapRepository.updateSortOrder(sortOrderMappings);
            },
            axis: 'y',
            containment: ".root-node"
        };

        $rootScope.downloadSelectedLayer = function() {
            if (activeLayerTool.hasActiveLayer()) {
                layerService.downloadData(activeLayerTool.getActiveLayer());
            }
        };

        $rootScope.downloadWorkingProject = function() {
            $window.open("/Project/DownloadWorkingProject");
        };

        $rootScope.clearShapesFromSelectedLayer = function() {
            var activeLayer = activeLayerTool.getActiveLayer();
            dialogBox.confirm({
                action: function() {
                    activeLayer.tools.clearFeatures.clear();
                    activeLayer.setMapExtent({ MaxX: 0, MinX: 0, MaxY: 0, MinY: 0 });
                },
                text: appMessages.confirm.clearShapes
            });
        };

        $rootScope.zoomToSelectedLayer = function() {
            mapTools.zoomToLayer.zoom(activeLayerTool.getActiveLayer());
        };

        $rootScope.deleteSelectedLayer = function() {

            if (!activeLayerTool.hasActiveLayer()) {
                return;
            }

            dialogBox.confirm({
                title: appMessages.confirm.removeLayerTitle,
                text: appMessages.confirm.removeLayer,
                action: function() {
                    var activeLayer = activeLayerTool.getActiveLayer();
                    var layerId = activeLayer.getId();
                    mapService.removeLayer(layerId);
                }
            });
        };

        $scope.showAttributeGrid = function() {
            $rootScope.isAttributeGridOn = true;
            $modal.open({
                templateUrl: './Templates/attributeGrid.html',
                controller: 'attributeGridController',
                backdrop: false,
                keyboard: false,
                windowClass: 'attributeGridModal',
                resolve: {
                    layerId: activeLayerTool.getActiveLayer().getId
                }
            }).result.then(function() {
                $rootScope.isAttributeGridOn = false;
            });
        }

        $scope.showVisualizationWindow = function() {
            $modal.open({
                templateUrl: './Templates/visualization.html',
                controller: 'visualizationController',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    surfLayer: activeLayerTool.getActiveLayer
                }
            }).result.then(function() {
                //$rootScope.isAttributeGridOn = false;
            });
        };

        $scope.toggleVisible = function(layer) {
            layer.IsVisible = !layer.IsVisible;
            layerService.saveVisibility(layer);
            layer.updateLayerVisibility();
            if (layer.tools.selectFeature.unselectAllFeatures) {
                layer.tools.selectFeature.unselectAllFeatures();
            }

        };

        $scope.toggleClassVisible = function(classObject, layer) {
            layerService.saveClassVisibility(layer, [classObject]);

        };

        $scope.toggleGroupVisibility = function(layer, group) {
            for (var index in group.classes) {
                group.classes[index].checked = group.isChecked;
            }
            layerService.saveClassVisibility(layer, group.classes);
        }

        $scope.enableClear = function() {
            if (activeLayerTool.hasActiveLayer()) {
                var activeLayer = activeLayerTool.getActiveLayer();
                return !activeLayer.isEmpty() && !$rootScope.isAttributeGridOn && activeLayer.isWritable() && !activeLayer.tools.deleteFeature.isNull;
            }
            return false;
        };

        $scope.enableZoom = function() {
            if (activeLayerTool.hasActiveLayer()) {
                var activeLayer = activeLayerTool.getActiveLayer();
                return !activeLayer.isEmpty() && activeLayer.IsVisible;
            }
            return false;
        };

        $scope.enableDownload = function() {
            return activeLayerTool.hasActiveLayer() && activeLayerTool.getActiveLayer().IsDataOwner && !activeLayerTool.getActiveLayer().isEmpty();
        };

        $scope.enableProperties = function() {
            return activeLayerTool.hasActiveLayer() && !$rootScope.isAttributeGridOn && !activeLayerTool.getActiveLayer().IsRaster && !activeLayerTool.getActiveLayer().IsPdf;
        };

        $scope.enableRemove = function() {
            return activeLayerTool.hasActiveLayer() && !$rootScope.isAttributeGridOn;
        };

        $scope.enableAttributeGrid = function() {
            return activeLayerTool.hasActiveLayer() && !$rootScope.isAttributeGridOn &&
                activeLayerTool.getActiveLayer().isSourceFileExists() && !activeLayerTool.getActiveLayer().IsRaster && !activeLayerTool.getActiveLayer().IsPdf &&
                !activeLayerTool.getActiveLayer().tools.selectFeature.isNull;
        };

        $scope.enableVisualization = function() {
            return activeLayerTool.hasActiveLayer() && !$rootScope.isAttributeGridOn;
        };

        $scope.enableDownloadProject = function() {
            return activeLayerTool.hasActiveLayer() && !allLayersUnOwned();
        };


        function allLayersUnOwned() {
            var layers = mapService.getLayers();
            for (var i in layers) {
                if (layers[i].IsDataOwner) {
                    return false;
                }
            }
            return true;
        }

        $scope.isActiveLayerEmpty = function() {
            if (activeLayerTool.hasActiveLayer()) {
                return activeLayerTool.getActiveLayer().isEmpty();
            }
            return true;
        };

        $scope.addBlankLayer = function() {
            $modal.open({
                templateUrl: '/static/layer/AddBlankLayer.html',
                controller: 'addBlankLayerCtrl',
                windowClass: 'blankLayerModal',
                backdrop: 'static',
                keyboard: false
            }).result.then(function(viewLayer) {
                mapService.addBlankLayer(viewLayer.name, viewLayer.shapeType);
            });
        };
    }
]);