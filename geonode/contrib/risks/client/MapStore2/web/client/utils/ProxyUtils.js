/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const ConfigUtils = require('./ConfigUtils');
const {isObject} = require('lodash');

var ProxyUtils = {
    needProxy: function(uri, config = {}) {
        var needed = false;
        var sameOrigin = !(uri.indexOf("http") === 0);
        var urlParts = !sameOrigin && uri.match(/([^:]*:)\/\/([^:]*:?[^@]*@)?([^:\/\?]*):?([^\/\?]*)/);
        if (urlParts) {
            let location = window.location;
            sameOrigin =
                urlParts[1] === location.protocol &&
                urlParts[3] === location.hostname;
            let uPort = urlParts[4];
            let lPort = location.port;
            if (uPort !== 80 && uPort !== "" || lPort !== "80" && lPort !== "") {
                sameOrigin = sameOrigin && uPort === lPort;
            }
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
                    needed = true;
                }
            }
        }
        return needed;
    },
    getProxyUrl: function(config = {}) {
        let proxyUrl = ConfigUtils.getProxyUrl(config);
        if (proxyUrl && isObject(proxyUrl)) {
            proxyUrl = proxyUrl.url;
        }
        return proxyUrl;
    }
};
module.exports = ProxyUtils;
