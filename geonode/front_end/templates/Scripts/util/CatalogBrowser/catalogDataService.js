appModule.factory("catalogDataService", [
    '$http',
    function ($http) {
        var catalogData;
        var rootUrl = window.urlRoot + "Catalog/";
        return {
            setData: function (catalogDataList) {
                catalogData = catalogDataList;
            },
            getData: function () {
                return catalogData;
            },
            getSharingDataModel: function (dataId) {
                return $http.get(rootUrl + 'GetSharingDataModel?dataId=' + dataId);
            },
            postSharing: function (dataId, userStates, emailStates) {
                return $http.post(rootUrl + 'Share', {
                    CanWrite: false,
                    DataId: dataId,
                    UserShareStates: userStates,
                    EmailShareStates: emailStates
                });
            },
            getUsedDataIds: function () {
                return $http.get(rootUrl + "GetDataIdsUsedInWorkingLayers");
            }
        };
    }]);
