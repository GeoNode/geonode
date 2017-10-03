appModule.factory('CSVEditorService', ['$http',
    function ($http) {
        var rootUrl = window.urlRoot + 'ExternalTable/';
        return {
            getCSVHeaders: function (dataId) {
                return $http.get(rootUrl + 'GetHeader?dataId=' + dataId);
            },
            getCSVData: function (dataRetrievalInfo) {
                return $http.post(rootUrl + 'GetDataPage', dataRetrievalInfo);
            },
            saveCSVDataChanges: function (data) {
                return $http.post(rootUrl + 'SaveRows', data);
            }
        }
    }
]);