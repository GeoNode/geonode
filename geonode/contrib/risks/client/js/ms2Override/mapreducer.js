/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var {CHANGE_MAP_VIEW, CHANGE_MOUSE_POINTER,
    CHANGE_ZOOM_LVL, CHANGE_MAP_CRS, CHANGE_MAP_SCALES, ZOOM_TO_EXTENT, PAN_TO,
    CHANGE_MAP_STYLE, CHANGE_ROTATION} = require('../../MapStore2/web/client/actions/map');
const {isArray} = require('lodash');


var assign = require('object-assign');
var MapUtils = require('../../MapStore2/web/client//utils/MapUtils');
var CoordinatesUtils = require('../../MapStore2/web/client//utils/CoordinatesUtils');

function mapConfig(state = null, action) {
    switch (action.type) {
        case CHANGE_MAP_VIEW:
            const {type, ...params} = action;
            return assign({}, state, params);
        case CHANGE_MOUSE_POINTER:
            return assign({}, state, {
                mousePointer: action.pointer
            });
        case CHANGE_ZOOM_LVL:
            return assign({}, state, {
                zoom: action.zoom,
                mapStateSource: action.mapStateSource
            });
        case CHANGE_MAP_CRS:
            return assign({}, state, {
                projection: action.crs
            });
        case CHANGE_MAP_SCALES:
            if (action.scales) {
                const dpi = state && state.mapOptions && state.mapOptions.view && state.mapOptions.view.DPI || null;
                const resolutions = MapUtils.getResolutionsForScales(action.scales, (state && state.projection) || "EPSG:4326", dpi);
                // add or update mapOptions.view.resolutions
                return assign({}, state, {
                    mapOptions: assign({}, state && state.mapOptions,
                        {
                            view: assign({}, state && state.mapOptions && state.mapOptions.view, {
                                resolutions: resolutions
                            })
                        })
                });
            } else if (state && state.mapOptions && state.mapOptions.view && state.mapOptions.view && state.mapOptions.view.resolutions) {
                // TODO: this block is removing empty objects from the state, check if it really needed
                // deeper clone
                let newState = assign({}, state);
                newState.mapOptions = assign({}, newState.mapOptions);
                newState.mapOptions.view = assign({}, newState.mapOptions.view);
                // remove resolutions
                delete newState.mapOptions.view.resolutions;
                // cleanup state
                if (Object.keys(newState.mapOptions.view).length === 0) {
                    delete newState.mapOptions.view;
                }
                if (Object.keys(newState.mapOptions).length === 0) {
                    delete newState.mapOptions;
                }
                return newState;
            }
            return state;
        case ZOOM_TO_EXTENT: {
            let zoom = 0;
            let extent = [];
            if (isArray(action.extent)) {
                extent = action.extent.map((val) => {
                    // MapUtils.getCenterForExtent returns an array of strings sometimes (catalog)
                    if (typeof val === 'string' || val instanceof String) {
                        return Number(val);
                    }
                    return val;
                });
            } else {
                extent = Object.keys(action.extent).map(v => {
                    if (typeof action.extent[v] === 'string' || action.extent[v] instanceof String) {
                        return Number(action.extent[v]);
                    }
                    return action.extent[v];
                });
            }
            let bounds = CoordinatesUtils.reprojectBbox(extent, action.crs, state.bbox && state.bbox.crs || "EPSG:4326");
            if (bounds) {
                // center by the max. extent defined in the map's config
                let center = CoordinatesUtils.reproject(MapUtils.getCenterForExtent(extent, action.crs), action.crs, 'EPSG:4326');
                // workaround to get zoom 0 for -180 -90... - TODO do it better
                let full = action.crs === "EPSG:4326" && extent && extent[0] <= -180 && extent[1] <= -90 && extent[2] >= 180 && extent[3] >= 90;
                if ( full ) {
                    zoom = 1;
                } else {
                    let mapBBounds = CoordinatesUtils.reprojectBbox(extent, action.crs, state.projection || "EPSG:4326");
                    // NOTE: STATE should contain size !!!
                    zoom = MapUtils.getZoomForExtent(mapBBounds, state.size, 0, 21, null) + 1;
                }
                let newbounds = {minx: bounds[0], miny: bounds[1], maxx: bounds[2], maxy: bounds[3]};
                let newbbox = assign({}, state.bbox, {bounds: newbounds});
                return assign({}, state, {
                    center,
                    zoom,
                    mapStateSource: action.mapStateSource,
                    bbox: newbbox
                });
            }
            return state;
        }
        case PAN_TO: {
            const center = CoordinatesUtils.reproject(
                action.center,
                action.center.crs,
                'EPSG:4326');
            return assign({}, state, {
                center
            });
        }
        case CHANGE_MAP_STYLE: {
            return assign({}, state, {mapStateSource: action.mapStateSource, style: action.style, resize: state.resize ? state.resize + 1 : 1});
        }
        case CHANGE_ROTATION: {
            let newBbox = assign({}, state.bbox, {rotation: action.rotation});
            return assign({}, state, {bbox: newBbox, mapStateSource: action.mapStateSource});
        }
        default:
            return state;
    }
}

module.exports = mapConfig;
