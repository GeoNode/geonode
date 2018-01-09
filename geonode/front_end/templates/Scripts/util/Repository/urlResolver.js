repositoryModule.factory('urlResolver', ['$location', function($location) {
    var geoserverRoot = 'http://localhost:8123/';
    var geoserverTileRoot = null;

    function resolve(controller, action, params) {
        window.urlRoot = 'api/';
        //window.urlRoot = '';
        var url = window.urlRoot + controller + "/" + action;

        url = addParams(url, params);

        return url;
    }

    function addParams(url, params) {
        if (angular.isDefined(params)) {
            if (typeof params === 'object') {
                url += "?";
                for (var key in params) {
                    url += ("&" + key + "=" + params[key]);
                }

                url = url.replace("?&", "?");
            } else {
                url += ('/' + params);
            }
        }

        return url;
    }

    function resolveAbsolute(controller, action, params) {
        var prefix = $location.protocol() + '://' + $location.host();
        var port = $location.port();
        if (port) {
            prefix += (':' + port);
        }
        return prefix + resolve(controller, action, params);
    }

    function resolveMapAbsolute(action, params) {
        return resolveAbsolute('Map', action, params);
    }

    function resolveGeoServer(service, params) {
        //window.urlRoot = '';
        
        params = params || {};
        if (window.isProxyEnabled) {
            return addParams(geoserverRoot + service, params);
        }
        //return resolve('GeoServerGateway', service, params);
        var url = geoserverRoot + 'geoserver' + "/" + service;
        url = addParams(url, params);
        return url;
    }

    return {
        resolveMap: function(action, params) {
            return resolve("Project", action, params);
        },
        resolveCatalog: function(action, params) {
            return resolve("Catalog", action, params);
        },
        resolveLayer: function(action, params) {
            return resolve("Layer", action, params);
        },
        resolveFeature: function(action, params) {
            return resolve("Feature", action, params);
        },
        resolveClassification: function(action, params) {
            return resolve("Classification", action, params);
        },
        resolveUserProfile: function(action, params) {
            return resolve("UserProfile", action, params);
        },
        resolveGeoserverTile: function(params) {
            return addParams(geoserverTileRoot, params);
        },
        getGeoServerTileRoot: function() {
            return geoserverTileRoot;
        },
        resolve: resolve,
        resolveRoot: function(urlPart, params) {
            var url = window.urlRoot + urlPart;
            url = addParams(url, params);
            return url;
        },
        resolveMapAbsolute: resolveMapAbsolute,
        resolveGeoServer: resolveGeoServer,
        setGeoserverRoot: function(root, tileRoot) {
            if (window.isProxyEnabled) {
                geoserverRoot = root;
            }
            geoserverTileRoot = tileRoot;

        }
    };
}]);