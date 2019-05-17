/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {MAP_CONFIG_LOADED, MAP_INFO_LOAD_START, MAP_INFO_LOADED, MAP_INFO_LOAD_ERROR, MAP_CONFIG_LOAD_ERROR} = require('../actions/config');
const {MAP_CREATED} = require('../actions/maps');

var assign = require('object-assign');
var ConfigUtils = require('../utils/ConfigUtils');

function mapConfig(state = null, action) {
    let map;
    switch (action.type) {
        case MAP_CONFIG_LOADED:
            let size = (state && state.map && state.map.present && state.map.present.size) || (state && state.map && state.map.size);

            let hasVersion = (action.config.version && action.config.version >= 2);
            // we get from the configuration what will be used as the initial state
            let mapState = (action.legacy && !hasVersion) ? ConfigUtils.convertFromLegacy(action.config) : ConfigUtils.normalizeConfig(action.config.map);

            mapState.map = assign({}, mapState.map, {mapId: action.mapId, size});
            // we store the map initial state for future usage
            return assign({}, mapState, {mapInitialConfig: mapState.map});
        case MAP_CONFIG_LOAD_ERROR:
            return {
                loadingError: action.error
            };
        case MAP_INFO_LOAD_START:
            map = state && state.map && state.map.present ? state.map.present : state && state.map;
            if (map && (map.mapId === action.mapId)) {
                map = assign({}, map, {info: {loading: true}});
                return assign({}, state, {map: map});
            }
            return state;
        case MAP_INFO_LOAD_ERROR: {
            map = state && state.map && state.map.present ? state.map.present : state && state.map;
            if (map && (map.mapId === action.mapId)) {
                map = assign({}, map, {info: {error: action.error}});
                return assign({}, state, {map: map});
            }
            return state;
        }
        case MAP_INFO_LOADED:
            map = state && state.map && state.map.present ? state.map.present : state && state.map;
            if (map && (map.mapId === action.mapId)) {
                map = assign({}, map, {info: action.info});
                return assign({}, state, {map: map});
            }
            return state;
        case MAP_CREATED: {
            map = state && state.map && state.map.present ? state.map.present : state && state.map;
            if (map && (!map.mapId)) {
                map = assign({}, map, {newMapId: action.resourceId});
                return assign({}, state, {map: map});
            }
        }
        default:
            return state;
    }
}

module.exports = mapConfig;
