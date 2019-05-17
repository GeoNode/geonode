/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const SELECT_FEATURES = 'SELECT_FEATURES';
const SET_FEATURES = 'SET_FEATURES';
const DOCK_SIZE_FEATURES = 'DOCK_SIZE_FEATURES';

function selectFeatures(features) {
    return {
        type: SELECT_FEATURES,
        features: features
    };
}

function setFeatures(features) {
    return {
        type: SET_FEATURES,
        features: features
    };
}

function dockSizeFeatures(dockSize) {
    return {
        type: DOCK_SIZE_FEATURES,
        dockSize: dockSize
    };
}

module.exports = {
    SELECT_FEATURES,
    SET_FEATURES,
    DOCK_SIZE_FEATURES,
    selectFeatures,
    setFeatures,
    dockSizeFeatures
};
