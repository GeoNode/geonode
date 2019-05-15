/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var axios = require('axios');
var ConfigUtils = require('../utils/ConfigUtils');
var toString = Object.prototype.toString;

const SecurityUtils = require('../utils/SecurityUtils');
const assign = require('object-assign');

/**
 * Internal helper that adds an extra paramater to an axios configuration.
 */
function addParameterToAxiosConfig(axiosConfig, parameterName, parameterValue) {
    // FIXME: the parameters can also be a URLSearchParams
    axiosConfig.params = assign({}, axiosConfig.params, {[parameterName]: parameterValue});
}

/**
 * Internal helper that adds or overrides an http header in a axios configuration.
 */
function addHeaderToAxiosConfig(axiosConfig, headerName, headerValue) {
    axiosConfig.headers = assign({}, axiosConfig.headers, {[headerName]: headerValue});
}

/**
 * Internal helper that will add to the axios config object the correct
 * authentication method based on the request URL.
 */
function addAuthenticationToAxios(axiosConfig) {
    if (!axiosConfig || !axiosConfig.url || !SecurityUtils.isAuthenticationActivated()) {
        return axiosConfig;
    }
    switch (SecurityUtils.getAuthenticationMethod(axiosConfig.url)) {
        case 'authkey':
            const token = SecurityUtils.getToken();
            if (!token) {
                return axiosConfig;
            }
            addParameterToAxiosConfig(axiosConfig, 'authkey', token);
            return axiosConfig;
        case 'basic':
            const basicAuthHeader = SecurityUtils.getBasicAuthHeader();
            if (!basicAuthHeader) {
                return axiosConfig;
            }
            addHeaderToAxiosConfig(axiosConfig, 'Authorization', basicAuthHeader);
            return axiosConfig;
        default:
            // we cannot handle the required authentication method
            return axiosConfig;
    }
}

function isArray(val) {
    return toString.call(val) === '[object Array]';
}
function isObject(val) {
    return val !== null && typeof val === 'object';
}
function isDate(val) {
    return toString.call(val) === '[object Date]';
}
function isArguments(val) {
    return toString.call(val) === '[object Arguments]';
}
function forEach(arg, fn) {
    var obj;

    // Check if arg is array-like
    const isArrayLike = isArray(arg) || isArguments(arg);

    // Force an array if not already something iterable
    if (typeof arg !== 'object' && !isArrayLike) {
        obj = [arg];
    } else {
        obj = arg;
    }

    // Iterate over array values
    if (isArrayLike) {
        for (let i = 0, l = obj.length; i < l; i++) {
            fn.call(null, obj[i], i, obj);
        }
    } else { // Iterate over object keys
        for (let key in obj) {
            if (obj.hasOwnProperty(key)) {
                fn.call(null, obj[key], key, obj);
            }
        }
    }
}
function buildUrl(argUrl, params) {
    var url = argUrl;
    var parts = [];

    if (!params) {
        return url;
    }

    forEach(params, function(argVal, argKey) {
        var val = argVal;
        var key = argKey;
        if (val === null || typeof val === 'undefined') {
            return;
        }

        if (isArray(val)) {
            key = key + '[]';
        }

        if (!isArray(val)) {
            val = [val];
        }

        forEach(val, function(argV) {
            var v = argV;
            if (isDate(v)) {
                v = v.toISOString();
            } else if (isObject(v)) {
                v = JSON.stringify(v);
            }
            parts.push(encodeURI(key) + '=' + encodeURIComponent(v));
        });
    });

    if (parts.length > 0) {
        url += (url.indexOf('?') === -1 ? '?' : '&') + parts.join('&');
    }
    return url;
}

axios.interceptors.request.use(config => {
    var uri = config.url || '';
    var sameOrigin = !(uri.indexOf("http") === 0);
    var urlParts = !sameOrigin && uri.match(/([^:]*:)\/\/([^:]*:?[^@]*@)?([^:\/\?]*):?([^\/\?]*)/);
    addAuthenticationToAxios(config);
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
                config.url = proxyUrl + encodeURIComponent(buildUrl(uri, config.params));
                config.params = undefined;
            }
        }
    }
    return config;
});

module.exports = axios;
