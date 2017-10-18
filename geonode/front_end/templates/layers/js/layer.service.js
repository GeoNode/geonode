(function() {
    angular
        .module('LayerApp')
        .factory('LayerService', LayerService);

    LayerService.$inject = ['$http', '$q'];

    function LayerService($http, $q) {
        return {
            getLayerByName: function(layerName) {
                return $http.get('layers/' + layerName + '/get');
            },
            getLayerFeatureByName: function(url, layerName) {
                var uri = encodeURIComponent(url + "?version=2.0.0&request=describeFeatureType&outputFormat=application/json&service=WFS&typeName=" + layerName);
                return $http.get('/proxy/?url=' + uri);
            },
            getFeatureDetails: function(url, layerName, propertyNames) {
                var uri = encodeURIComponent(url + "?version=2.0.0&request=GetFeature&outputFormat=application/json&service=WFS&typeNames=" + layerName + "&propertyName=" + propertyNames);
                return $http.get('/proxy/?url=' + uri);
            }
        };
    }
})();