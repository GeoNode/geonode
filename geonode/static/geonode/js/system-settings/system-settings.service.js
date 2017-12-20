(function () {
    angular
        .module('SystemSettingsApp')
        .factory('SettingsService', SettingsService);

    SettingsService.$inject = ['$http', '$q', '$cookies'];

    function SettingsService($http, $q, $cookies) {

        var layerSettings = {};

        function get(url) {
            var deferred = $q.defer();
            $http.get(url)
                .success(function (res) {
                    deferred.resolve(res);
                }).error(function (error, status) {
                deferred.reject({error: error, status: status});
            });
            return deferred.promise;
        }

        return {
            getLayers: function (url) {
                return get('/api/layers/');
            },
            getSystemSettings: function(url){
                return get('/settings/api/system/settings/');
            },
            saveSystemSettings: function(url){

            }

        }

    }
})();
