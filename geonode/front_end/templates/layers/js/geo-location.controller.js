(function() {
    'use strict';

    angular
        .module('LayerApp')
        .controller('GeoLocationController', GeoLocationController);

    GeoLocationController.$inject = ['FileUploader', '$timeout', 'uiGridConstants'];

    function GeoLocationController(FileUploader, $timeout, uiGridConstants) {
        var self = this;

        function initialize() {
            self.fileHeaders = [];
            self.headers = ['post_code', 'road_no', 'house_no'];
            self.mappedHeaders = {};

            self.gridOptions = {
                paginationPageSizes: [25, 50, 75, 100],
                paginationPageSize: 25,
                data: [],
                minRowsToShow: 15,
                enableGridMenu: true,
                exporterCsvFilename: 'address_layer.csv',
                // exporterCsvLinkElement: angular.element(document.querySelectorAll(".custom-csv-link-location")),
                enableHorizontalScrollbar: uiGridConstants.scrollbars.ALWAYS
            };

            self.isSuccess = false;
            self.isError = false;
            self.Message = {
                Success: "",
                Error: ""
            };
        }

        self.file = new FileUploader({
            url: '/layers/api/geo-location/',
            headers: {
                'X-CSRFToken': csrftoken
            },
            formData: [self.mappedHeaders],
            filters: [{
                name: 'extension',
                fn: function(item) {
                    var fileExtension = item.name.split('.').pop();
                    if (fileExtension !== 'csv') {
                        self.isError = true;
                        self.Message.Error = "Currently supported .csv file only.";
                    }
                    return fileExtension === 'csv';
                }
            }],
            onAfterAddingFile: function(item) {
                if (self.file.queue.length > 1) {
                    self.file.removeFromQueue(0);
                }
                var fileReader = new FileReader();
                fileReader.onloadend = function() {
                    var lines = this.result.split(/\r\n|\n/);
                    $timeout(function() {
                        self.fileHeaders = lines[0].split(',');
                        for (var i = 0; i < self.fileHeaders.length; i++) {
                            self.fileHeaders[i] = self.fileHeaders[i].split('"')[1];
                        }
                    });
                };
                fileReader.readAsText(item._file);
            },
            onBeforeUploadItem: function(item) {
                item.formData = [self.mappedHeaders];
            }
        });

        self.file.onSuccessItem = function(item, response, status, headers) {
            if (response.success) {
                self.isSuccess = true;
                self.Message.Success = "Success on: " + response.success + " rows";
            }
            if (response.error) {
                self.isError = true;
                self.Message.Error = "Error on: " + response.error + " rows";
            }

            self.propertyNames = [];
            // var headers = response.splice(0,0);
            var data = response.data;
            for (var k in data[0]) {
                self.propertyNames.push(k);
            }
            self.gridOptions.data = data;
            self.gridOptions.columnDefs = [];
            self.propertyNames.forEach(function(e) {
                self.gridOptions.columnDefs.push({
                    field: e,
                    displayName: e
                });
            });
        };

        self.upload = function() {
            if (self.file.queue.length) {
                self.file.uploadItem(0);
            }

        };

        (initialize)();
    }

})();