(function() {
    'use strict';

    angular
        .module('LayerApp')
        .controller('FeaturePreviewController', FeaturePreviewController);

    FeaturePreviewController.$inject = ['data', '$modalInstance', 'uiGridConstants', 'AngularUiGridOptions'];

    function FeaturePreviewController(data, $modalInstance, uiGridConstants, AngularUiGridOptions) {
        var self = this;

        function initializeTabs() {
            self.tabs = Object.keys(data).map(function(e) {
                return {
                    name: e,
                    active: false
                };
            });
            self.tabs[0].active = true;
        }

        function initializeData() {
            self.data = {};
            for (var d in data) {
                self.data[d] = {};
                self.data[d].gridOptions = new AngularUiGridOptions();
                self.data[d].gridOptions.exporterCsvFilename = d + '.csv';
                
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

        self.init = function() {
            initializeTabs();
            initializeData();
        };
    }
})();