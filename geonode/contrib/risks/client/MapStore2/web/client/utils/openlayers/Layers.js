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

    createLayer: function(type, options, map, mapId) {
        var layerCreator = layerTypes[type];
        if (layerCreator) {
            return layerCreator.create(options, map, mapId);
        }
        return null;
    },
    updateLayer: function(type, layer, newOptions, oldOptions, map, mapId) {
        var layerCreator = layerTypes[type];
        if (layerCreator && layerCreator.update) {
            return layerCreator.update(layer, newOptions, oldOptions, map, mapId);
        } else if (oldOptions && layer && layer.getSource() && layer.getSource().updateParams) {
            // old method, keept for compatibility.
            // TODO move it in specific layerCreator where possibile
            let changed = false;
            if (oldOptions.params && newOptions.params) {
                changed = Object.keys(oldOptions.params).reduce((found, param) => {
                    if (newOptions.params[param] !== oldOptions.params[param]) {
                        return true;
                    }
                    return found;
                }, false);
            } else if (!oldOptions.params && newOptions.params) {
                changed = true;
            }

            if (changed) {
                layer.getSource().updateParams(newOptions.params);
            }
        }
    },
    removeLayer: function(type, options, map, mapId, layer) {
        var layerCreator = layerTypes[type];
        if (layerCreator && layerCreator.remove) {
            return layerCreator.remove(options, map, mapId, layer);
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
    isValid(type, layer) {
        var layerCreator = layerTypes[type];
        if (layerCreator && layerCreator.isValid) {
            return layerCreator.isValid(layer);
        }
        return true;
    }
};

module.exports = Layers;
