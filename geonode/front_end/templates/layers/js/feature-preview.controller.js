(function() {
    'use strict';

    angular
        .module('LayerApp')
        .controller('FeaturePreviewController', FeaturePreviewController);

    FeaturePreviewController.$inject = ['data', 'wfsConfig', '$modalInstance', 'uiGridConstants', 'AngularUiGridOptions', 'LayerService', '$modal', '$window', 'layerService', 'mapService'];

    function FeaturePreviewController(data, wfsConfig, $modalInstance, uiGridConstants, AngularUiGridOptions, LayerService, $modal, $window, layerService, mapService) {
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

        function initializeData() {
            self.data = {};
            for (var d in data) {
                self.data[d] = {};
                self.data[d].gridOptions = new AngularUiGridOptions();
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
                    var layer_name = res.url.split('/').pop();

                    var layer = layerService.map({
                        name: layer_name,
                        geoserverUrl: $window.GeoServerTileRoot + '?access_token=' + $window.access_token
                    });
                    mapService.addDataLayer(layer);

                });
            });
        }
    }
})();