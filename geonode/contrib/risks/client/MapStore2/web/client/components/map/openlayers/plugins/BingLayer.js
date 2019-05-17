/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var Layers = require('../../../../utils/openlayers/Layers');
var ol = require('openlayers');

const checkLoaded = (layer, options) => {
    if (layer.getSource && layer.getSource().getState() === 'error') {
        if (options.onError) {
            options.onError(layer);
        }
    }
    if (layer.getSource && layer.getSource().getState() === 'loading') {
        setTimeout(checkLoaded.bind(null, layer, options), 1000);
    }
};

Layers.registerType('bing', {
    create: (options) => {
        var key = options.apiKey;
        var maxNativeZoom = options.maxNativeZoom || 19;
        const layer = new ol.layer.Tile({
            preload: Infinity,
            opacity: options.opacity !== undefined ? options.opacity : 1,
            zIndex: options.zIndex,
            visible: options.visibility,
            source: new ol.source.BingMaps({
              key: key,
              imagerySet: options.name,
              maxZoom: maxNativeZoom
            })
        });
        setTimeout(checkLoaded.bind(null, layer, options), 1000);
        return layer;
    },
    isValid: (layer) => {
        if (layer.getSource && layer.getSource().getState() === 'error') {
            return false;
        }
        return true;
    }
});
