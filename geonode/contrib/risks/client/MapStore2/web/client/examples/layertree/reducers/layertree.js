/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var {SHOW_SETTINGS, HIDE_SETTINGS, UPDATE_OPACITY} = require('../actions/layertree');

var assign = require('object-assign');

var initialState = {
    Settings: {
        expanded: false,
        node: null,
        nodeType: null,
        options: {
            opacity: 1.0
        }
    }
};

function layertree(state = initialState, action) {
    switch (action.type) {
        case SHOW_SETTINGS: {
            let settings = assign({}, state.Settings, {expanded: true, node: action.node, nodeType: action.nodeType, options: action.options});

            return assign({}, state, {
                Settings: settings
            });
        }
        case HIDE_SETTINGS: {
            let settings = assign({}, state.Settings, {expanded: false, node: null, nodeType: null, options: {}});

            return assign({}, state, {
                Settings: settings
            });
        }
        case UPDATE_OPACITY: {
            let settings = assign({}, state.Settings, {options: {opacity: action.opacity / 100.0}});

            return assign({}, state, {
                Settings: settings
            });
        }
        default:
            return state;
    }
}

module.exports = layertree;
