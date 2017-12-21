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

        function put(url, data) {
            $http.put(url, data, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            })
                .then(
                    function (response) {
                        // success callback
                        //console.log(response);
                    },
                    function (response) {
                        // failure callback
                    }
                );
        }

        return {
            getLayers: function (url) {
                return get('/api/layers/');
            },
            getSystemSettings: function (url) {
                return get('/settings/api/system/settings/');
            },
            saveSystemSettings: function (data) {
                return put('/settings/api/settings/save/', data);
            }

        }

    }
})();
