/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var {TOGGLE_GRATICULE, UPDATE_MARKER} = require('../actions/controls');
var assign = require('object-assign');

const initialState = {
    graticule: false,
    marker: null
};

function controls(state = initialState, action) {
    switch (action.type) {
        case TOGGLE_GRATICULE: {
            return assign({}, state,
                {
                    graticule: !state.graticule
                }
            );
        }
        case UPDATE_MARKER: {
            return assign({}, state,
                {
                    marker: action.point
                }
            );
        }
        default:
            return state;
    }
}

module.exports = controls;
