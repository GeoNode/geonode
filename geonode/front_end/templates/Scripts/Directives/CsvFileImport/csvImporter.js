angular.module('csvImport', ['truncateModule']).directive('csvImporter', [
    function () {
        return {
            restrict: 'E',
            transclude: true,
            scope: {
                importer: '=',
            },
            templateUrl: 'Scripts/Directives/CsvFileImport/csvFileImport.html',
            controller: ['$scope', '$timeout', 'csvImportService', function ($scope, $timeout, service) {
                var csvDetails;
                var fileReadComplete;

                $scope.validate = function (model) {
                    model.isInvalid = !$scope.importer.validator(model, $scope.csvHeaders);
                };

                $scope.loadHeaders = function () {
                    if (!fileReadComplete) return;

                    if ($scope.useFirstRowAsHeader) {
                        $scope.csvHeaders = angular.copy(csvDetails.csvHeaders);
                    } else {
                        $scope.csvHeaders = angular.copy(csvDetails.customHeaders);
                    }

                    $scope.csvRows = angular.copy(csvDetails.rows);
                    if ($scope.useFirstRowAsHeader) {
                        $scope.csvRows.splice(0, 1);
                    }
                    for (var i in $scope.csvHeaders) {
                        if ($scope.importer.onValueInit) {
                            $scope.importer.onValueInit($scope.csvHeaders[i]);
                        } else {
                            $scope.csvHeaders[i].mappedName = $scope.csvHeaders[i].name;
                        }
                    }
                    $scope.importer.onHeaderChange();
                    validateAllFields();
                };

                function validateAllFields() {
                    for (var j in $scope.csvHeaders) {
                        $scope.validate($scope.csvHeaders[j]);
                    }
                }

                $scope.importer.fieldsInvalid = function () {
                    for (var i in $scope.csvHeaders) {
                        if ($scope.csvHeaders[i].isInvalid) return true;
                    }
                    return false;
                };

                $scope.importer.getNameMappings = function () {
                    return {
                        useFirstRowAsHeader: $scope.useFirstRowAsHeader || false,
                        mappings: service.getHeaderMapping($scope.csvHeaders, $scope.importer.requiredHeaders)
                    }
                };

                (function readAndExtractCsvFile() {
                    var reader = new FileReader();
                    reader.onload = function (e) {
                        var fileContent = reader.result;
                        fileReadComplete = true;
                        csvDetails = service.getCsvDetails(fileContent);
                        $timeout(function () {
                            $scope.$apply(function () {
                                $scope.loadHeaders();
                            });
                        });
                    };
                    reader.readAsText($scope.importer.csvFile);
                })();
            }]
        }
    }
]).directive('csvPreview', [function () {
    return {
        restrict: 'AE',
        templateUrl: 'Scripts/Directives/CsvFileImport/csvPreview.html',
        scope: {
            headers: '=',
            rows: '='
        }
    }
}]).factory('csvImportService', [function () {
    return {
        getCsvDetails: function (fileContent) {
            //https://github.com/gkindel/CSV-JS
            CSV.RELAXED = true;
            var rows = CSV.parse(fileContent);
            var csvHeaders = [], customHeaders = [];

            if (rows.length == 0) return { csvHeaders: [], customHeaders: [] };

            var headers = rows[0];
            var uniqueHeaderKeys = {};
            for (var i in headers) {
                uniqueHeaderKeys[headers[i].toString()] = true;
            }
            for (var j in uniqueHeaderKeys) {
                csvHeaders.push({ name: j });
            }
            var columnNamePrefix = "Column";
            for (var l = 0; l < rows[0].length; l++) {
                customHeaders.push({ name: columnNamePrefix + (l + 1) });
            }

            return { csvHeaders: csvHeaders, customHeaders: customHeaders, rows: rows.splice(0, 4) }
        },
        getHeaderMapping: function (csvHeaders, requiredHeaders) {
            var mappings = angular.copy(requiredHeaders);
            for (var i in csvHeaders) {
                if (!csvHeaders[i].includeColumn) continue;
                var item = _.findWhere(mappings, { name: csvHeaders[i].mappedName });
                if (item) {
                    var itemIndex = _.indexOf(mappings, item);
                    mappings[itemIndex].nameInFile = csvHeaders[i].name;
                    mappings[itemIndex].index = i;
                    csvHeaders[i].isTaken = true;
                }
            }

            for (var j in csvHeaders) {
                if (!csvHeaders[j].isTaken && csvHeaders[j].includeColumn) {
                    mappings.push({ name: csvHeaders[j].mappedName, nameInFile: csvHeaders[j].name, index: j });
                }
            }

            return mappings;
        }

    }
}]).filter('showBlank', [function () {
    return function (value) {
        if (value === "" || value === undefined) {
            return "<Blank>";
        }
        return value;
    };
}]);