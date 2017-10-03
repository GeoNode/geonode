appModule.controller('CSVEditorController', [
    '$scope', 'CSVEditorService', '$modalInstance', 'dataId', 'isReadOnly', 'surfToastr', function ($scope, CSVEditorService, $modalInstance, dataId, isReadOnly, surfToastr) {

        $scope.pagination = { totalItems: 0, currentPage: 1, itemsPerPage: 5, pageSizes: [5, 10, 50, 100] };
        $scope.csvData = { headers: [], rows: [] };
        $scope.data = { loading: true, isReadonly: isReadOnly };
        var nullData;
        var lastEditingRow = {};

        $scope.postData = { DataId: dataId, DeletedIds: [], EditedRows: [], AddedRows: [] };

        function stopLoading() {
            $scope.data.loading = false;
        }

        (function getHeaders() {
            CSVEditorService.getCSVHeaders(dataId).success(function (headerInfo) {
                $scope.csvData.headers = headerInfo.Headers;
                $scope.pagination.totalItems = headerInfo.TotalNumberOfRows;
                nullData = [];
                for (var i = 0; i < $scope.csvData.headers.length; i++) {
                    nullData.push(null);
                }
                getPagedDataFromServer(1, stopLoading, stopLoading);
            }).error(function () {
                stopLoading();
            });
        })();

        function getPagedDataFromServer(currentPage, onSuccess, onError) {
            var currentPageSize = $scope.pagination.itemsPerPage;
            var startIndex = currentPageSize * currentPage - currentPageSize;

            CSVEditorService.getCSVData({
                StartIndex: startIndex, NumberOfItems: currentPageSize,
                DataId: dataId
            }).success(function (rows) {
                $scope.csvData.rows = rows;
                removeDeletedRows();
                changeEditedRows();
                if (onSuccess) {
                    onSuccess();
                }
            }).error(function () {
                if (onError) {
                    onError();
                }
            });
        }

        $scope.itemPerPageChanged = function () {
            populateEditedRows();
            lastEditingRow.isEditing = false;
            $scope.pagination.currentPage = 1;
            getPagedDataFromServer();
        }

        $scope.onPageSelect = function (currentPage) {
            populateEditedRows();
            lastEditingRow.isEditing = false;
            getPagedDataFromServer(currentPage);
        }

        $scope.addRow = function () {
            lastEditingRow.isEditing = false;
            var newRow = { isEditing: true, Data: angular.copy(nullData) };
            $scope.postData.AddedRows.push(newRow);
            lastEditingRow = newRow;
        }

        function changeEditedRows() {
            for (var j in $scope.postData.EditedRows) {
                var editedItem = _.findWhere($scope.csvData.rows, { Id: $scope.postData.EditedRows[j].Id });
                if (editedItem) {
                    editedItem.Data = $scope.postData.EditedRows[j].Data;
                    editedItem.isDirty = true;
                }
            }
        }

        function removeDeletedRows() {
            for (var k in $scope.postData.DeletedIds) {
                var deletedItem = _.findWhere($scope.csvData.rows, { Id: $scope.postData.DeletedIds[k] });
                if (deletedItem) {
                    $scope.csvData.rows = _.without($scope.csvData.rows, deletedItem);
                }
            }
        }

        function populateEditedRows() {
            for (var l in $scope.csvData.rows) {
                if ($scope.csvData.rows[l].isDirty) {
                    var editedItem = _.findWhere($scope.postData.EditedRows, { Id: $scope.csvData.rows[l].Id });
                    if (editedItem) {
                        editedItem.Data = $scope.csvData.rows[l].Data;
                    } else {
                        $scope.postData.EditedRows.push({
                            Id: $scope.csvData.rows[l].Id,
                            Data: $scope.csvData.rows[l].Data
                        });
                    }
                }
            }
        }

        $scope.makeEditable = function (row) {
            lastEditingRow.isEditing = false;
            row.isEditing = true;
            lastEditingRow = row;
        }

        $scope.deleteRow = function (index) {
            lastEditingRow.isEditing = false;

            dialogBox.confirm({
                title: appMessages.confirm.confirmHeader,
                text: appMessages.confirm.deleteItem,
                action: function () {
                    var item = $scope.csvData.rows.splice(index, 1)[0];
                    $scope.postData.DeletedIds.push(item.Id);
                }
            });
        }

        $scope.deleteAddedRow = function (index) {
            dialogBox.confirm({
                title: appMessages.confirm.confirmHeader,
                text: appMessages.confirm.deleteItem,
                action: function () {
                    $scope.postData.AddedRows.splice(index, 1);
                }
            });
        }

        $scope.saveChanges = function () {
            populateEditedRows();
            CSVEditorService.saveCSVDataChanges($scope.postData).success(function () {
                $modalInstance.close();
                surfToastr.success(appMessages.toastr.changesSaved());
            }).error(function () {

            });
        }

        $scope.closeCSVEditor = function () {
            $modalInstance.dismiss('close');
        }
    }
]);