/**
 * Copyright 2015-2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {
    MAPS_LIST_LOADED, MAPS_LIST_LOADING, MAPS_LIST_LOAD_ERROR, MAP_CREATED, MAP_UPDATING,
    MAP_METADATA_UPDATED, MAP_DELETING, MAP_DELETED, ATTRIBUTE_UPDATED, PERMISSIONS_LIST_LOADING,
    PERMISSIONS_LIST_LOADED, SAVE_MAP, PERMISSIONS_UPDATED, THUMBNAIL_ERROR, RESET_UPDATING,
    MAPS_SEARCH_TEXT_CHANGED} = require('../actions/maps');
const MAP_TYPE_CHANGED = "MAP_TYPE_CHANGED"; // NOTE: this is from home action in product. move to maps actions when finished;
const assign = require('object-assign');
const _ = require('lodash');

function maps(state = {
    mapType: "leaflet",
    enabled: false,
    errors: [],
    searchText: ""}, action) {
    switch (action.type) {
        case MAP_TYPE_CHANGED: {
            return assign({}, state, {
                mapType: action.mapType
            });
        }
        case MAPS_SEARCH_TEXT_CHANGED: {
            return assign({}, state, {
                searchText: action.text
            });
        }
        case MAPS_LIST_LOADING:
            return assign({}, state, {
                loading: true,
                start: action.params && action.params.start,
                limit: action.params && action.params.limit,
                searchText: action.searchText
            });
        case MAPS_LIST_LOADED:
            if (action.maps && action.maps.results && Array.isArray(action.maps.results)) {
                return assign({}, state, action.maps, {
                    loading: false,
                    start: action.params && action.params.start,
                    limit: action.params && action.params.limit,
                    searchText: action.searchText
                });
            }
            let results = action.maps.results !== "" ? [action.maps.results] : [];
            return assign({}, state, action.maps, {results, loading: false});
        case MAPS_LIST_LOAD_ERROR:
            return {
                loadingError: action.error
            };
        case MAP_UPDATING: {
            let newMaps = (state.results === "" ? [] : [...state.results] );

            for (let i = 0; i < newMaps.length; i++) {
                if (newMaps[i].id && newMaps[i].id === action.resourceId ) {
                    newMaps[i] = assign({}, newMaps[i], {updating: true});
                }
            }
            return assign({}, state, {results: newMaps});
        }
        case MAP_METADATA_UPDATED: {
            let newMaps = (state.results === "" ? [] : [...state.results] );

            for (let i = 0; i < newMaps.length; i++) {
                if (newMaps[i].id && newMaps[i].id === action.resourceId ) {
                    newMaps[i] = assign({}, newMaps[i], {description: action.newDescription, name: action.newName, updating: false});
                }
            }
            return assign({}, state, {results: newMaps});
        }
        case ATTRIBUTE_UPDATED: {
            let newMaps = (state.results === "" ? [] : [...state.results] );
            for (let i = 0; i < newMaps.length; i++) {
                if (newMaps[i].id && newMaps[i].id === action.resourceId) {
                    newMaps[i] = assign({}, newMaps[i], {[action.name]: decodeURIComponent(action.value), updating: false, loadingError: action.error ? action.error : null}); // TODO remove decodeURIComponent to reuse this reducer!!!
                }
            }
            return assign({}, state, {results: newMaps});
        }
        case PERMISSIONS_UPDATED: {
            let newMaps = (state.results === "" ? [] : [...state.results] );
            for (let i = 0; i < newMaps.length; i++) {
                if (newMaps[i].id && newMaps[i].id === action.resourceId) {
                    newMaps[i] = assign({}, newMaps[i], { loadingError: action.error ? action.error : null});
                }
            }
            return assign({}, state, {results: newMaps});
        }
        case MAP_DELETING: {
            let newMaps = (state.results === "" ? [] : [...state.results] );

            for (let i = 0; i < newMaps.length; i++) {
                if (newMaps[i].id && newMaps[i].id === action.resourceId ) {
                    newMaps[i] = assign({}, newMaps[i], {deleting: true});
                }
            }
            return assign({}, state, {results: newMaps});
        }
        case MAP_DELETED: {
            let newMaps = (state.results === "" ? [] : [...state.results] );
            let newMapsState = {
                results: newMaps.filter(function(el) {
                    return el.id && el.id !== action.resourceId;
                }),
                totalCount: state.totalCount - 1
            };

            return assign({}, state, newMapsState);
        }
        case MAP_CREATED: {
            let newMaps = (state.results === "" ? [] : [...state.results] );
            let newMapsState = {
                results: [...newMaps, action.metadata],
                totalCount: state.totalCount + 1
            };
            return assign({}, state, newMapsState);
        }
        case SAVE_MAP: {
            let newMaps = (state.results === "" ? [] : [...state.results] );

            for (let i = 0; i < newMaps.length; i++) {
                if (newMaps[i].id && newMaps[i].id === action.resourceId ) {
                    newMaps[i] = assign({}, newMaps[i], {
                        files: action.map && action.map.files,
                        errors: action.map && action.map.errors,
                        newThumbnail: action.map && action.map.newThumbnail,
                        thumbnailError: action.map && action.map.thumbnailError,
                        thumbnail: action.map && action.map.thumbnail });
                }
            }
            return assign({}, state, {results: newMaps});
        }
        case THUMBNAIL_ERROR: {
            let newMaps = (state.results === "" ? [] : [...state.results] );

            for (let i = 0; i < newMaps.length; i++) {
                if (newMaps[i].id && newMaps[i].id === action.resourceId ) {
                    newMaps[i] = assign({}, newMaps[i], {updating: false});
                }
            }
            return assign({}, state, {results: newMaps});
        }
        case RESET_UPDATING: {
            let newMaps = (state.results === "" ? [] : [...state.results] );

            for (let i = 0; i < newMaps.length; i++) {
                if (newMaps[i].id && newMaps[i].id === action.resourceId ) {
                    newMaps[i] = assign({}, newMaps[i], {updating: false});
                }
            }
            return assign({}, state, {results: newMaps});
        }
        case PERMISSIONS_LIST_LOADING: {
            let newMaps = (state.results === "" ? [] : [...state.results] );
            // TODO: Add the fix for GeoStore single-item arrays
            let newState = assign({}, state, {
                results: newMaps.map(function(map) {
                        if (map.id === action.mapId) {
                            return assign({}, map, {permissionLoading: true});
                        }
                        return map;
                    })
                }
            );
            return newState;
        }
        case PERMISSIONS_LIST_LOADED: {
            let newMaps = (state.results === "" ? [] : [...state.results] );
            // TODO: Add the fix for GeoStore single-item arrays
            let newState = assign({}, state, {
                results: newMaps.map(function(map) {
                        if (map.id === action.mapId) {

                            // Fix to overcome GeoStore bad encoding of single object arrays
                            let fixedSecurityRule = [];
                            if (action.permissions && action.permissions.SecurityRuleList && action.permissions.SecurityRuleList.SecurityRule) {
                                if ( _.isArray(action.permissions.SecurityRuleList.SecurityRule)) {
                                    fixedSecurityRule = action.permissions.SecurityRuleList.SecurityRule;
                                } else {
                                    fixedSecurityRule.push(action.permissions.SecurityRuleList.SecurityRule);
                                }
                            }

                            return assign({}, map, {
                                permissionLoading: false,
                                permissions: {
                                SecurityRuleList: {
                                    SecurityRule: fixedSecurityRule
                                }
                            }});
                        }
                        return map;
                    })
                }
            );
            return newState;
        }
        default:
            return state;
    }
}

module.exports = maps;
