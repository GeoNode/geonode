/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {
    HIGHLIGHT_STATUS,
    UPDATE_HIGHLIGHTED
} = require('../actions/highlight');


const initialState = {
    status: 'disabled',
    layer: 'featureselector',
    features: [],
    highlighted: 0
};

function highlight(state = initialState, action) {
    switch (action.type) {
        case HIGHLIGHT_STATUS: {
            return {...state, status: action.status};
        }
        case UPDATE_HIGHLIGHTED: {
            return {...state, highlighted: action.features.length, features: action.features, status: action.status || state.status};
        }
        default:
            return state;
    }
}

module.exports = highlight;
