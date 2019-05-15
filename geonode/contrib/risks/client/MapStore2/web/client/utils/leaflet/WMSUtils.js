/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var objectAssign = require('object-assign');

var WMSUtils = {
    PARAM_OPTIONS: ["layers", "styles", "format", "transparent", "version", "tiled" ],
    wmsToLeafletOptions: function(options) {
        var opacity = options.opacity !== undefined ? options.opacity : 1;
        // NOTE: can we use opacity to manage visibility?
        return objectAssign({
            layers: options.name,
            styles: options.style || "",
            format: options.format || 'image/png',
            transparent: options.transparent !== undefined ? options.transparent : true,
            tiled: options.tiled !== undefined ? options.tiled : true,
            opacity: opacity
        }, options.params || {});
    },
    getWMSURL: function( url ) {
        return url.split("\?")[0];
    },
    filterWMSParamOptions(options) {
        let paramOptions = {};
        Object.keys(options).forEach((key) => {
            if (!key || !key.toLowerCase) {
                return;
            }
            if (WMSUtils.PARAM_OPTIONS.indexOf(key.toLowerCase()) >= 0) {
                paramOptions[key] = options[key];
            }
        });
        return paramOptions;
    }
};

module.exports = WMSUtils;
