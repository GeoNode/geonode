/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const SHOW_SETTINGS = 'SHOW_SETTINGS';
const HIDE_SETTINGS = 'HIDE_SETTINGS';
const UPDATE_OPACITY = 'UPDATE_OPACITY';

function showSettings(node, nodeType, options) {
    return {
        type: SHOW_SETTINGS,
        node: node,
        nodeType: nodeType,
        options: options
    };
}

function hideSettings() {
    return {
        type: HIDE_SETTINGS
    };
}

function updateOpacity(opacity) {
    return {
        type: UPDATE_OPACITY,
        opacity
    };
}

module.exports = {SHOW_SETTINGS, HIDE_SETTINGS, UPDATE_OPACITY,
        showSettings, hideSettings, updateOpacity};
