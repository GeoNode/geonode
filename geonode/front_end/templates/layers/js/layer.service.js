(function() {
    angular
        .module('LayerApp')
        .factory('LayerService', LayerService);

    LayerService.$inject = ['$http', '$q'];

    function LayerService($http, $q) {
        function get(url) {
            var deferred = $q.defer();
            $http.get(url)
                .success(function(res) {
                    deferred.resolve(res);
                }).error(function(error, status) {
                    deferred.reject({ error: error, status: status });
                });
            return deferred.promise;
        }
        return {
            getGeoServerSettings: function() {
                return get('api/geoserver-settings/');
            },
            getLayerByName: function(layerName) {
                return get('layers/' + layerName + '/get');
            },
            getWFS: function(url, params, useProxy) {
                url = url + "wfs/?service=WFS";
                for (var k in params) {
                    url += '&' + k + '=' + params[k];
                }
                var uri = url;
                if(useProxy == undefined || useProxy){
                    uri = '/proxy/?url=' + encodeURIComponent(url);
                }
                return get(uri);
                
            },
            getLayerFeatureByName: function(url, layerName) {
                return this.getWFS(url, {
                    typeName: layerName,
                    request: "describeFeatureType",
                    version: "2.0.0",
                    outputFormat: "application/json"

                });
            },
            getFeatureDetails: function(url, layerName, propertyNames) {
                return this.getWFS(url, {
                    typeNames: layerName,
                    request: "GetFeature",
                    propertyName: propertyNames,
                    version: "2.0.0",
                    outputFormat: "application/json"

                });
            }
            
        };
    }
})();