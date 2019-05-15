/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Proj4js = require('proj4');
var React = require('react');
var url = require('url');

var axios = require('axios');

const {isArray} = require('lodash');
const assign = require('object-assign');

const epsg4326 = Proj4js ? new Proj4js.Proj('EPSG:4326') : null;
const centerPropType = React.PropTypes.shape({
    x: React.PropTypes.number.isRequired,
    y: React.PropTypes.number.isRequired,
    crs: React.PropTypes.string
});

const {isObject} = require('lodash');

const urlQuery = url.parse(window.location.href, true).query;

const isMobile = require('ismobilejs');

let localConfigFile = 'localConfig.json';

let defaultConfig = {
    proxyUrl: "/mapstore/proxy/?url=",
    geoStoreUrl: "/mapstore/rest/geostore/",
    printUrl: "/mapstore/print/info.json",
    translationsPath: "translations",
    bingApiKey: null,
    mapquestApiKey: null
};

var ConfigUtils = {
    defaultSourceType: "gxp_wmssource",
    backgroundGroup: "background",

    PropTypes: {
        center: centerPropType,
        config: React.PropTypes.shape({
            center: centerPropType,
            zoom: React.PropTypes.number.isRequired
        }),
        mapStateSource: React.PropTypes.string
    },
    getDefaults: function() {
        return defaultConfig;
    },
    setLocalConfigurationFile(file) {
        localConfigFile = file;
    },
    loadConfiguration: function() {
        return axios.get(localConfigFile).then(response => {
            if (typeof response.data === 'object') {
                defaultConfig = assign({}, defaultConfig, response.data);
            }
            return defaultConfig;
        });
    },

    getCenter: function(center, projection) {
        var retval;
        if ((center.x || center.x === 0) && (center.y || center.y === 0) && center.crs) {
            if (center.crs !== "EPSG:4326") {
                let xy = Proj4js.toPoint([center.x, center.y]);
                const epsgMap = new Proj4js.Proj(center.crs);
                Proj4js.transform(epsgMap, epsg4326, xy);
                retval = {y: xy.y, x: xy.x, crs: "EPSG:4326"};
            } else {
                retval = center;
            }
            return retval;
        }
        let xy = Proj4js.toPoint(center);
        if (projection) {
            const epsgMap = new Proj4js.Proj(projection);
            Proj4js.transform(epsgMap, epsg4326, xy);
        }
        return {y: xy.y, x: xy.x, crs: "EPSG:4326"};
    },
    normalizeConfig: function(config) {
        const {layers, groups, plugins, ...other} = config;
        other.center = ConfigUtils.getCenter(other.center);
        return {
            map: other,
            layers: layers.map(ConfigUtils.setApiKeys, config).map(ConfigUtils.setLayerId).map(ConfigUtils.setUrlPlaceholders),
            groups: groups,
            plugins: plugins
        };
    },
    getUserConfiguration: function(defaultName, extension, geoStoreBase) {
        return ConfigUtils.getConfigurationOptions(urlQuery, defaultName, extension, geoStoreBase);
    },
    getConfigurationOptions: function(query, defaultName, extension, geoStoreBase) {
        const mapId = query.mapId;
        let configUrl;
        if (mapId) {
            configUrl = ( geoStoreBase || defaultConfig.geoStoreUrl ) + "data/" + mapId;
        } else {
            configUrl = (query.config || defaultName || 'config') + '.' + (extension || 'json');
        }
        return {
            configUrl: configUrl,
            legacy: !!mapId
        };
    },

    convertFromLegacy: function(config) {
        var mapConfig = config.map;
        var sources = config.gsSources || config.sources;
        var layers = mapConfig.layers.filter(layer => sources[layer.source]);
        var latLng = ConfigUtils.getCenter(mapConfig.center, mapConfig.projection);
        var zoom = mapConfig.zoom;
        var maxExtent = mapConfig.maxExtent || mapConfig.extent;

        // setup layers and sources with defaults
        this.setupSources(sources, config.defaultSourceType);
        this.setupLayers(layers, sources, ["gxp_osmsource", "gxp_wmssource", "gxp_googlesource", "gxp_bingsource", "gxp_mapquestsource", "gxp_olsource"]);
        return ConfigUtils.normalizeConfig({
            center: latLng,
            zoom: zoom,
            maxExtent: maxExtent, // TODO convert maxExtent
            layers: layers,
            projection: mapConfig.projection || 'EPSG:3857'
        });
    },

    /**
     * set default wms source
     */
    setupSources: function(sources, defaultSourceType) {
        var defType = defaultSourceType;
        var source;
        if (!defaultSourceType) {
            defType = this.defaultSourceType;
        }
        for (source in sources) {
            if (sources.hasOwnProperty(source)) {
                if (!sources[source].ptype) {
                    sources[source].ptype = defType;
                }
            }
        }
    },
    normalizeSourceUrl: function(sourceUrl) {
        if (sourceUrl && sourceUrl.indexOf('?') !== -1) {
            return sourceUrl.split('?')[0];
        }
        return sourceUrl;
    },
    /**
     * Copy important source options to layer options.
     */
    copySourceOptions: function(layer, source) {
        layer.baseParams = source.baseParams;
        if (source.url) {
            let sourceParts = url.parse(source.url, true);
            for (let k in sourceParts.query) {
                if (k.toUpperCase() === "REQUEST" ) {
                    delete sourceParts.query[k];
                }
            }
            layer.baseParams = assign({}, layer.baseParams, sourceParts.query);
        }
        layer.url = ConfigUtils.normalizeSourceUrl(source.url);
    },

    /**
     * Setup the layer visibility for the background group.
     * if background layers are not visible, sets the last one
     */
    setupLayers: function(layers, sources, supportedSourceTypes) {
        // setup background visibility
        var candidateVisible;
        var i; var layer; var source;
        for (i = 0; i < layers.length; i++) {
            layer = layers[i];
            source = sources[layer.source];
            if (source) {
                ConfigUtils.copySourceOptions(layer, source);
            }

            let type = source.ptype;
            if (type) {
                layer.type = type.replace(/^gxp_(.*)source$/i, "$1");
            } else {
                layer.type = 'unknown';
            }
            if (layer) {
                if (supportedSourceTypes.indexOf(source && source.ptype) >= 0) {
                    if (layer.group === this.backgroundGroup) {
                        // force to false if undefined
                        layer.visibility = layer.visibility || false;
                        if (candidateVisible && candidateVisible.visibility) {
                            /* if more than one layer is visible in the background group
                               shows only the last one hiding the previous.
                            */
                            if (layer.visibility) {
                                candidateVisible.visibility = false;
                                candidateVisible = layer;
                            }
                        } else {
                            candidateVisible = layer;
                        }
                    }
                } else {
                    layer.visibility = false;
                }
            }
        }
        // set the candidate visible
        if (candidateVisible) {
            candidateVisible.visibility = true;
        }
    },
    /**
     * Utility to merge different configs
     */
    mergeConfigs: function(baseConfig, mapConfig) {
        baseConfig.map = mapConfig.map;
        baseConfig.gsSources = mapConfig.gsSources || mapConfig.sources;
        return baseConfig;
    },
    getProxyUrl: function(config) {
        return config.proxyUrl ? config.proxyUrl : defaultConfig.proxyUrl;
    },
    getProxiedUrl: function(uri, config = {}) {
        let sameOrigin = !(uri.indexOf("http") === 0);
        let urlParts = !sameOrigin && uri.match(/([^:]*:)\/\/([^:]*:?[^@]*@)?([^:\/\?]*):?([^\/\?]*)/);
        // ajax.addAuthenticationToAxios(config);
        if (urlParts) {
            let location = window.location;
            sameOrigin =
                urlParts[1] === location.protocol &&
                urlParts[3] === location.hostname;
            let uPort = urlParts[4];
            let lPort = location.port;
            let defaultPort = location.protocol.indexOf("https") === 0 ? 443 : 80;
            uPort = uPort === "" ? defaultPort + "" : uPort + "";
            lPort = lPort === "" ? defaultPort + "" : lPort + "";
            sameOrigin = sameOrigin && uPort === lPort;
        }
        if (!sameOrigin) {
            let proxyUrl = ConfigUtils.getProxyUrl(config);
            if (proxyUrl) {
                let useCORS = [];
                if (isObject(proxyUrl)) {
                    useCORS = proxyUrl.useCORS || [];
                    proxyUrl = proxyUrl.url;
                }
                const isCORS = useCORS.reduce((found, current) => found || uri.indexOf(current) === 0, false);
                if (!isCORS) {
                    return proxyUrl + encodeURIComponent(uri);
                }
            }
        }
        return uri;
    },
    /**
    * Utility to detect browser properties.
    * Code from leaflet-src.js
    */
    getBrowserProperties: function() {

        let ie = 'ActiveXObject' in window;
        let ielt9 = ie && !document.addEventListener;
        let ie11 = ie && (window.location.hash === !!window.MSInputMethodContext && !!document.documentMode);

        // terrible browser detection to work around Safari / iOS / Android browser bugs
        let ua = navigator.userAgent.toLowerCase();
        let webkit = ua.indexOf('webkit') !== -1;
        let chrome = ua.indexOf('chrome') !== -1;
        let phantomjs = ua.indexOf('phantom') !== -1;
        let android = ua.indexOf('android') !== -1;
        let android23 = ua.search('android [23]') !== -1;
        let gecko = ua.indexOf('gecko') !== -1;

        let mobile = isMobile.any; // typeof window.orientation !== undefined + '';
        let msPointer = !window.PointerEvent && window.MSPointerEvent;
        let pointer = (window.PointerEvent && window.navigator.pointerEnabled && window.navigator.maxTouchPoints) ||
                  msPointer;
        let retina = ('devicePixelRatio' in window && window.devicePixelRatio > 1) ||
                 ('matchMedia' in window && window.matchMedia('(min-resolution:144dpi)') &&
                  window.matchMedia('(min-resolution:144dpi)').matches);

        let doc = document.documentElement;
        let ie3d = ie && ('transition' in doc.style);
        let webkit3d = ('WebKitCSSMatrix' in window) && ('m11' in new window.WebKitCSSMatrix()) && !android23;
        let gecko3d = 'MozPerspective' in doc.style;
        let opera3d = 'OTransition' in doc.style;
        let any3d = !window.L_DISABLE_3D && (ie3d || webkit3d || gecko3d || opera3d) && !phantomjs;

        let touch = !window.L_NO_TOUCH && !phantomjs && (pointer || 'ontouchstart' in window ||
        (window.DocumentTouch && document instanceof window.DocumentTouch));

        return {
        ie: ie,
        ie11: ie11,
        ielt9: ielt9,
        webkit: webkit,
        gecko: gecko && !webkit && !window.opera && !ie,

        android: android,
        android23: android23,

        chrome: chrome,

        ie3d: ie3d,
        webkit3d: webkit3d,
        gecko3d: gecko3d,
        opera3d: opera3d,
        any3d: any3d,

        mobile: mobile,
        mobileWebkit: mobile && webkit,
        mobileWebkit3d: mobile && webkit3d,
        mobileOpera: mobile && window.opera,

        touch: touch,
        msPointer: msPointer,
        pointer: pointer,

        retina: retina
        };
    },
    setApiKeys: function(layer) {
        if (layer.type === 'bing') {
            layer.apiKey = this.bingApiKey || defaultConfig.bingApiKey;
        }
        if (layer.type === 'mapquest') {
            layer.apiKey = this.mapquestApiKey || defaultConfig.mapquestApiKey;
        }
        return layer;
    },
    setUrlPlaceholders: function(layer) {
        if (layer.url) {
            if (isArray(layer.url)) {
                layer.url = layer.url.map((currentUrl) => {
                    return ConfigUtils.replacePlaceholders(currentUrl);
                });
            } else {
                layer.url = ConfigUtils.replacePlaceholders(layer.url);
            }
        }
        return layer;
    },
    replacePlaceholders: function(inputUrl) {
        let currentUrl = inputUrl;
        (currentUrl.match(/\{.*?\}/g) || []).forEach((placeholder) => {
            currentUrl = currentUrl.replace(placeholder, defaultConfig[placeholder.substring(1, placeholder.length - 1)] || '');
        });
        return currentUrl;
    },
    setLayerId: function(layer, i) {
        if (!layer.id) {
            layer.id = layer.name + "__" + i;
        }
        return layer;
    },
    getConfigProp: function(prop) {
        return defaultConfig[prop];
    },
    setConfigProp: function(prop, value) {
        defaultConfig[prop] = value;
    },
    removeConfigProp: function(prop) {
        delete defaultConfig[prop];
    }
};

module.exports = ConfigUtils;
