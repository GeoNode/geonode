appModule.controller('csvHeaderMappingController', [
    '$scope', '$modalInstance', 'file', '$timeout', 'csvHeaderMappingService', 'surfToastr',
    function ($scope, $modalInstance, file, $timeout, csvHeaderMappingService, surfToastr) {

        $scope.validation = { message: null };

        $scope.csvFileImporter = {
            csvFile: file,
            requiredHeaders: [
                { name: "Street" },
                { name: "City" },
                { name: "State" },
                { name: "Zip_code" }
            ],
            onValueInit: function (model) {
                model.mappedName = csvHeaderMappingService.getValidName(model.name);
            },
            validator: function (model, headers) {
                $scope.validation.message = csvHeaderMappingService.getValidationMessage(model.mappedName);
                var isFieldValid = !$scope.validation.message;

                if (!$scope.validation.message) {
                    $scope.validation.message = csvHeaderMappingService.getUniqueNameValidationMessage(headers);
                }
                return isFieldValid;
            },
            onHeaderChange: function() {
                $scope.validation.message = null;
            },
            showPreview: true
        }

        $scope.csvHeaders = [];

        $scope.validateMapping = function (selectedName, index) {
            for (var i in $scope.headers) {
                if (i != index && $scope.headers[i].nameInFile == selectedName) {
                    surfToastr.error("The header is already mapped with a different field. Please select a different one or change that first.");
                    $scope.headers[index].nameInFile = null;
                    return;
                }
            }
        };

        $scope.closeModal = function () {
            $modalInstance.close();
        }

        $scope.done = function () {
            $modalInstance.close($scope.csvFileImporter.getNameMappings());
        }
    }
]);
