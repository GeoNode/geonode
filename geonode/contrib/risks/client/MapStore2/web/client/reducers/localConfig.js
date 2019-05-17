/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {LOCAL_CONFIG_LOADED} = require('../actions/localConfig');

const assign = require('object-assign');
const ConfigUtils = require('../utils/ConfigUtils');
const initialState = ConfigUtils.getDefaults();
function controls(state = initialState, action) {
    switch (action.type) {
        case LOCAL_CONFIG_LOADED:
            return assign({}, state, action.config);
        default:
            return state;
    }
}

module.exports = controls;
