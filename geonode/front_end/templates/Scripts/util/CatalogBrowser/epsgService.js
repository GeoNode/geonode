appModule.factory('epsgService', [
    '$http', 'urlResolver',
    function ($http, urlResolver) {
        var knownEpsgCodeSet = {};

        $http.get(urlResolver.resolveCatalog('GetKnownEpsgCodes')).success(function (allowedCodes) {
            for (var i in allowedCodes) {
                knownEpsgCodeSet[allowedCodes[i]] = true;
            }
        });

        return {
            isEpsgKnown: function (epsgCode) {
                return !!knownEpsgCodeSet[epsgCode];
            }
        };
    }
]);