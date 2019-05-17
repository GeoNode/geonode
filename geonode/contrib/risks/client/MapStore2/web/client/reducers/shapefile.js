/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {
    ON_SHAPE_CHOOSEN,
    ON_SHAPE_ERROR,
    ON_SELECT_LAYER,
    SHAPE_LOADING,
    ON_LAYER_ADDED,
    UPDATE_SHAPE_BBOX,
    ON_SHAPE_SUCCESS
} = require('../actions/shapefile');

const {TOGGLE_CONTROL} = require('../actions/controls');

const assign = require('object-assign');

const initialState = {
    layers: null,
    error: null,
    loading: false,
    selected: null,
    bbox: [190, 190, -190, -190]
};

function shapefile(state = initialState, action) {
    switch (action.type) {
        case ON_SHAPE_CHOOSEN: {
            let selected = (action.layers && action.layers[0]) ? action.layers[0] : null;
            return assign({}, state, {layers: action.layers, selected: selected, bbox: [190, 190, -190, -190]});
        }
        case ON_SHAPE_ERROR: {
            return assign({}, state, {error: action.message, success: null});
        }
        case SHAPE_LOADING: {
            return assign({}, state, {loading: action.status});
        }
        case ON_SELECT_LAYER: {
            return assign({}, state, {selected: action.layer});
        }
        case ON_LAYER_ADDED: {
            let newLayers = state.layers.filter((l) => {
                return action.layer.name !== l.name;
            }, this);
            let selected = (newLayers && newLayers[0]) ? newLayers[0] : null;
            return assign({}, state, {layers: newLayers, selected: selected}, !selected ? {bbox: [190, 190, -190, -190]} : {});
        }
        case UPDATE_SHAPE_BBOX: {
            return assign({}, state, {bbox: action.bbox});
        }
        case ON_SHAPE_SUCCESS: {
            return assign({}, state, {success: action.message, error: null});
        }
        case TOGGLE_CONTROL: {
            if (action.control === 'shapefile') {
                return assign({}, state, {error: null, success: null});
            }
            return state;
        }
        default:
            return state;
    }
}

module.exports = shapefile;
