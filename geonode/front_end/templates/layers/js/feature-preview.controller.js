(function() {
    'use strict';

    angular
        .module('LayerApp')
        .controller('FeaturePreviewController', FeaturePreviewController);

    FeaturePreviewController.$inject = ['$scope','data', 'wfsConfig', '$modalInstance', 'uiGridConstants', 'AngularUiGridOptions', 'LayerService', '$modal', '$window', 'layerService', 'mapService','attributeGridService', 'surfToastr'];

    function FeaturePreviewController(scope,data, wfsConfig, $modalInstance, uiGridConstants, AngularUiGridOptions, LayerService, $modal, $window, layerService, mapService,attributeGridService, surfToastr) {
        var self = this;

        function initializeTabs() {
            self.tabs = Object.keys(data).map(function(e) {
                return {
                    name: e,
                    active: false
                };
            });
            self.tabs[0].active = true;
            self.selectedTab = self.tabs[0];
        }

        self.gridApi={};

        function getRequestObjectToGetFeature(featureID) {
            var requestObj = {
                request: 'GetFeature',
                typeName: self.selectedTab.name,
                maxFeatures: 1,
                featureID: featureID,
                version: '2.0.0',
                outputFormat: 'json',
                exceptions: 'application/json'
            };
            return requestObj;
        }

        function initializeData() {
            self.data = {};
            for (var d in data) {
                self.data[d] = {};
                self.data[d].gridOptions = new AngularUiGridOptions();
                self.data[d].gridOptions.multiSelect= false;
                self.data[d].gridOptions.onRegisterApi= function (gridApi) {
                    self.gridApi[d] = gridApi;        
                    gridApi.selection.on.rowSelectionChanged(scope, function(rows) {
                        scope.selectedFeatures = gridApi.selection.getSelectedRows();
                        if(scope.selectedFeatures.length>0){
                            var featureId=scope.selectedFeatures[0].Feature_Id;
                            var requestObj = getRequestObjectToGetFeature(featureId);
                            LayerService.getWFSWithGeom('api/geoserver/', requestObj, false).then(function(response) {
                                attributeGridService.highlightFeature(response);
                            });
                        }
                    });
                };
                self.data[d].gridOptions.exporterCsvFilename = d + '.csv';
                if (data[d].length == 0)
                    continue;
                self.data[d].gridOptions.columnDefs = Object.keys(data[d][0]).map(function(e) {
                    return {
                        field: e,
                        displayName: e
                    };
                });
                self.data[d].gridOptions.data = data[d];
            }
        }

        self.closeDialog = function() {
            $modalInstance.close();
        };

        self.SaveAsLayer = function() {
            showLayerSaveDialog();

        };

        self.init = function() {
            initializeTabs();
            initializeData();
        };

        function showLayerSaveDialog() {
            $modal.open({
                templateUrl: '/static/layers/_layers-save.html',
                controller: 'LayerSaveController as ctrl',
                backdrop: 'static',
                keyboard: false,
                windowClass: 'fullScreenModal First'
            }).result.then(function(res) {
                LayerService.createLayerByWfs(Object.assign({}, wfsConfig, {
                    typeNames: self.selectedTab.name
                }, res)).then(function(res){
                    surfToastr.success('Layer Created successfully', 'Success');
                    
                    var layer_name = res.url.split('/').pop();

                    var layer = layerService.map({
                        name: layer_name,
                        geoserverUrl: $window.GeoServerTileRoot + '?access_token=' + $window.mapConfig.access_token
                    });
                    mapService.addDataLayer(layer);

                });
            });
        }
    }
})();