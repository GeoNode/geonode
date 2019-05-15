/**
 * Copyright 2015-2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {CLICK_ON_MAP} = require('../actions/map');

const {
    ERROR_FEATURE_INFO,
    EXCEPTIONS_FEATURE_INFO,
    LOAD_FEATURE_INFO,
    CHANGE_MAPINFO_STATE,
    NEW_MAPINFO_REQUEST,
    PURGE_MAPINFO_RESULTS,
    CHANGE_MAPINFO_FORMAT,
    SHOW_MAPINFO_MARKER,
    HIDE_MAPINFO_MARKER,
    SHOW_REVERSE_GEOCODE,
    HIDE_REVERSE_GEOCODE,
    GET_VECTOR_INFO
} = require('../actions/mapInfo');

const {RESET_CONTROLS} = require('../actions/controls');

const assign = require('object-assign');
const {head} = require('lodash');

function receiveResponse(state, action, type) {
    const request = head((state.requests || []).filter((req) => req.reqId === action.reqId));
    if (request) {
        const responses = state.responses || [];
        return assign({}, state, {
            responses: [...responses, {
                response: action[type],
                queryParams: action.requestParams,
                layerMetadata: action.layerMetadata
            }]
        });
    }
    return state;
}

function mapInfo(state = {}, action) {
    switch (action.type) {
        case CHANGE_MAPINFO_STATE:
            return assign({}, state, {
                enabled: action.enabled
            });
        case NEW_MAPINFO_REQUEST: {
            const {reqId, request} = action;
            const requests = state.requests || [];
            return assign({}, state, {
                requests: [...requests, {request, reqId}]
            });
        }
        case PURGE_MAPINFO_RESULTS:
            return assign({}, state, {
                responses: [],
                requests: []
            });
        case LOAD_FEATURE_INFO: {
            return receiveResponse(state, action, 'data');
        }
        case EXCEPTIONS_FEATURE_INFO: {
            return receiveResponse(state, action, 'exceptions');
        }
        case ERROR_FEATURE_INFO: {
            return receiveResponse(state, action, 'error');
        }
        case CLICK_ON_MAP: {
            return assign({}, state, {
                clickPoint: action.point
            });
        }
        case CHANGE_MAPINFO_FORMAT: {
            return assign({}, state, {
                infoFormat: action.infoFormat
            });
        }
        case SHOW_MAPINFO_MARKER: {
            return assign({}, state, {
                showMarker: true
            });
        }
        case HIDE_MAPINFO_MARKER: {
            return assign({}, state, {
                showMarker: false
            });
        }
        case SHOW_REVERSE_GEOCODE: {
            return assign({}, state, {
                showModalReverse: true,
                reverseGeocodeData: action.reverseGeocodeData
            });
        }
        case HIDE_REVERSE_GEOCODE: {
            return assign({}, state, {
                showModalReverse: false,
                reverseGeocodeData: undefined
            });
        }
        case RESET_CONTROLS: {
            return assign({}, state, {
                showMarker: false,
                responses: [],
                requests: []
            });
        }
        case GET_VECTOR_INFO: {
            const buffer = require('turf-buffer');
            const intersect = require('turf-intersect');
            const point = {
              "type": "Feature",
              "properties": {},
              "geometry": {
                "type": "Point",
                "coordinates": [action.request.lng, action.request.lat]
              }
            };
            let unit = action.metadata && action.metadata.units;
            switch (unit) {
                case "m":
                    unit = "meters";
                    break;
                case "deg":
                    unit = "degrees";
                    break;
                case "mi":
                    unit = "miles";
                    break;
                default:
                    unit = "meters";
            }
            let resolution = action.metadata && action.metadata.resolution || 1;
            let bufferedPoint = buffer(point, (action.metadata.buffer || 1) * resolution, unit);
            const intersected = action.layer.features.filter(
                    (feature) => {
                        try {
                            // TODO: instead of create a fixed buffer, we should check the feature style to create the proper buffer.
                            return intersect(bufferedPoint, (resolution && action.metadata.buffer && unit) ? buffer(feature, 1, "meters") : feature);
                        }catch(e) {
                            return false;
                        }
                    }

            );
            const responses = state.responses || [];
            return assign({}, state, {
                requests: [...state.requests, {}],
                responses: [...responses, {
                    response: {
                        crs: null,
                        features: intersected,
                        totalFeatures: "unknown",
                        type: "FeatureCollection"
                    },
                    queryParams: action.request,
                    layerMetadata: action.metadata,
                    format: 'JSON'
                }]
            });
        }
        default:
            return state;
    }
}

module.exports = mapInfo;
