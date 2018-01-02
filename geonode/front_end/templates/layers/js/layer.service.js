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
        function getDefaultStyle(){
            return {
                "Name": "",
                "default": {
                    "fillPattern": null,
                    "textFillColor": "#0000ff",
                    "text": null,
                    "pixelDensity": null,
                    "strokeDashstyle": "solid",
                    "strokeWidth": 1.0,
                    "strokeColor": "#000000",
                    "strokeOpacity": null,
                    "fillOpacity": 0.75,
                    "fillColor": "#ffffff",
                    "pointRadius": 14.0,
                    "graphicName": "circle",
                    "textGraphicName": null,
                    "externalGraphic": null,
                },
                "select": {
                    "fillPattern": "",
                    "textFillColor": "#0000ff",
                    "text": null,
                    "pixelDensity": null,
                    "strokeDashstyle": "solid",
                    "strokeWidth": 1.0,
                    "strokeColor": "#000000",
                    "strokeOpacity": 1.0,
                    "fillOpacity": 0.4,
                    "fillColor": "#ff00ff",
                    "pointRadius": 6.0,
                    "graphicName": "circle",
                    "textGraphicName": null,
                    "externalGraphic": null,
                },
                "labelConfig": {
                    "attribute": null,
                    "visibilityZoomLevel": 0,
                    "font": "Times",
                    "fontStyle": "normal",
                    "fontWeight": "normal",
                    "color": "#000000",
                    "borderColor": "#ffffff",
                    "showBorder": true,
                    "size": 10.0,
                    "alignment": 1.0,
                    "offsetX": 0.0,
                    "offsetY": 0.0,
                    "rotation": 0.0,
                    "followLine": false,
                    "repeat": false,
                    "repeatInterval": 5.0,
                    "wrap": false,
                    "wrapPixel": 50.0
                },
                "classifierDefinitions": {}
            };
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
                if (useProxy == undefined || useProxy) {
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
            },
            getStyleByLayer: function(layerName) {
                return get('/layers/' + layerName + '/style/');
            },
            getStylesByLayer: function(layerName) {
                return get('/layers/' + layerName + '/styles/');
            },
            getStyle: function(id) {
                return get('/layers/style/' + id + '/');
            },
            getNewStyle : function(){
                return getDefaultStyle();
            }
        };
    }
})();