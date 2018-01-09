
(function() {
    angular
        .module('LayerApp')
        .factory('LayerService', LayerService);

    LayerService.$inject = ['$http', '$q', '$window'];

    function LayerService($http, $q, $window) {
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

        function put(url, obj) {
            var deferred = $q.defer();
            $http.put(url, obj, {
                headers: {
                    "X-CSRFToken": $cookies.get('csrftoken')
                }
            }).success(function(res) {
                deferred.resolve(res);
            }).error(function(error, status) {
                deferred.reject({ error: error, status: status });
            });
            return deferred.promise;
        }

        function _uuid() {
            function _() {
                var rand = Math.ceil(1e15 + Math.random() * 1e5).toString(16);
                return rand.substring(rand.length - 4);
            }
            return _() + _() + '-' + _() + '-' + _() + '-' + _() + '-' + _() + _();

        }

        function getDefaultStyle() {
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
                var deferred = $q.defer();
                get('/layers/style/' + id + '/').then(function(res) {
                    var style = JSON.parse(res.json_field);
                    style.id = res.id;
                    if (!style) {
                        style = getNewStyle();
                    }
                    style.Name = res.uuid;
                    style.default.userStyle = style.Name;
                    style.select.userStyle = style.Name;
                    deferred.resolve(style);
                }, function() {
                    deferred.reject({});
                });
                return deferred.promise;
            },
            getNewStyle: function() {
                return getDefaultStyle();
            },
            getLayerByMap: function(mapId, layerName) {
                return get('/maps/' + mapId + '/layer/' + layerName + '/');
            },
            updateLayerByMap: function(mapId, layerName, obj) {
                return put('/maps/' + mapId + '/layer/' + layerName + '/', obj);
            },
            getAttributesName: function(layerName) {
                var deferred = $q.defer();
                this.getLayerFeatureByName($window.GeoServerHttp2Root , layerName).then(function(res) {
                    res.featureTypes.forEach(function(featureType) {
                        var attributes = [];
                        featureType.properties.forEach(function(e) {
                            if (e.name !== 'the_geom') {
                                attributes.push({
                                    "Id": e.name,
                                    "Name": e.name,
                                    "AttributeName": null,
                                    "IsPublished": true,
                                    "Type": e.localType,
                                    "Length": 92,
                                    "Precision": null,
                                    "Scale": null
                                });
                            }
                        }, this);
                        deferred.resolve(attributes);
                    }, this);
                });
                return deferred.promise;
            },
            getShapeType: function(layerName) {
                var deferred = $q.defer();
                this.getLayerFeatureByName($window.GeoServerHttp2Root , layerName).then(function(res) {
                    res.featureTypes.forEach(function(featureType) {
                        var shapeType = "";
                        featureType.properties.forEach(function(e) {
                            if (e.name === 'the_geom') {
                                if (e.localType.toLowerCase().search('polygon') != -1)
                                    shapeType = 'polygon';
                                else if (e.localType.toLowerCase().search('point') != -1)
                                    shapeType = 'point';
                                else if (e.localType.toLowerCase().search('linestring') != -1)
                                    shapeType = 'polyline';
                                deferred.resolve(shapeType);
                                return;
                            }
                        }, this);
                    }, this);
                });
                return deferred.promise;
            }
        };
    }
})();