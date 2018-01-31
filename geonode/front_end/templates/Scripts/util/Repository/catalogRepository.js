repositoryModule.factory('catalogRepository', [
    '$http', 'urlResolver',
    function ($http, urlResolver) {

        return {
            deleteData: function (dataId) {
                return $http.post(urlResolver.resolveCatalog('Delete'), { dataId: dataId });
            }
        };
    }
]);