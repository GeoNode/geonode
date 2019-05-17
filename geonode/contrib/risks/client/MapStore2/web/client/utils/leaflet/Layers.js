/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const layerTypes = {};

var Layers = {

    registerType: function(type, impl) {
        layerTypes[type] = impl;
    },

    createLayer: function(type, options) {
        var layerCreator = layerTypes[type];
        if (layerCreator && layerCreator.create) {
            return layerCreator.create(options);
        } else if (layerCreator) {
            // TODO this compatibility workaround should be removed
            // using the same interface
            return layerCreator(options);
        }
        return null;
    },
    renderLayer: function(type, options, map, mapId, layer) {
        var layerCreator = layerTypes[type];
        if (layerCreator && layerCreator.render) {
            return layerCreator.render(options, map, mapId, layer);
        }
        return null;
    },
    updateLayer: function(type, layer, newOptions, oldOptions) {
        var layerCreator = layerTypes[type];
        if (layerCreator && layerCreator.update) {
            return layerCreator.update(layer, newOptions, oldOptions);
        }
    },
    isValid(type, layer) {
        var layerCreator = layerTypes[type];
        if (layerCreator && layerCreator.isValid) {
            return layerCreator.isValid(layer);
        }
        return true;
    }
};

module.exports = Layers;
