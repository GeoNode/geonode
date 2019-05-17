/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const SAVE_PLUGIN_CONFIG = 'SAVE_PLUGIN_CONFIG';
const COMPILE_ERROR = 'COMPILE_ERROR';

function savePluginConfig(plugin, cfg) {
    return {
        type: SAVE_PLUGIN_CONFIG,
        plugin,
        cfg
    };
}

function compileError(message) {
    return {
        type: COMPILE_ERROR,
        message
    };
}

function resetError() {
    return {
        type: COMPILE_ERROR,
        message: null
    };
}

module.exports = {SAVE_PLUGIN_CONFIG, COMPILE_ERROR, savePluginConfig, compileError, resetError};
