mapModule.factory('surfFeatureFactory', [
    '$http', 'urlResolver', 'geometryColumnName', '$q', 'SurfFeature',
    function ($http, urlResolver, geometryColumnName, $q, SurfFeature) {
        var wfsParams = {
            service: 'wfs',
            version: "2.0.0",
            outputFormat: 'json',
            request: 'GetFeature',
            maxFeatures: 1,
            count: 1,
            //propertyName: geometryColumnName,
            //typeNames: '',
            //featureID: ''

        };
        var format = new ol.format.GeoJSON();

        var urlRoot = urlResolver.resolveGeoServer('wfs');

        function upsertToCache(surfLayer, fid, olFeature) {
            surfLayer.olFeatures[fid] = olFeature;
        }

        function createSurfFeature(olFeature, surfLayer) {
            var surfFeature = new SurfFeature(olFeature, surfLayer);
            surfFeature.olFeature = olFeature;
            return surfFeature;
        }

        function getCompleteFeature(surfFeature) {
            var surfLayer = surfFeature.layer;
            var fid = surfFeature.getFid();
            var olFeatureFromCache = surfLayer.olFeatures[fid];

            if (olFeatureFromCache) {
                var defered = $q.defer();
                defered.resolve(olFeatureFromCache);
                return defered.promise;
            } else {
                return getFromServer(surfLayer.DataId, fid).then(function (olFeature) {
                    upsertToCache(surfLayer, fid, olFeature);
                    return olFeature;
                });
            }
        }

        function getFromServer(layerFileId, fid) {
            var params = angular.extend({ typeNames: layerFileId, featureID: fid }, wfsParams);
            return $http({
                url: urlRoot,
                method: 'GET',
                params: params
            }).then(function (response) {
                var features = format.readFeatures(response.data);
                return features[0];
            });
        }

        function deleteFromCache(surfLayer, fid) {
            delete surfLayer.olFeatures[fid];
        }

        function getFeatureFromUrl(url, surfLayer) {
            if (url) {
                var parser = new ol.format.GML2();
                return $http.get(url).then(function(response) {
                    var olFeatures = parser.readFeatures(response.data);
                    return olFeatures.map(function(olFeature) {
                        return {
                            surfFeature: new SurfFeature(olFeature, surfLayer),
                            olFeature: olFeature
                        };
                    });
                });
            } else {
                var differed = $q.defer();
                differed.reject();
                return differed.promise;
            }
        }

        return {
            getFeatureFromUrl: getFeatureFromUrl,
            getCompleteFeature: getCompleteFeature,
            upsertToCache: upsertToCache,
            createSurfFeature: createSurfFeature,
            deleteFromCache: deleteFromCache
        };
    }
]);