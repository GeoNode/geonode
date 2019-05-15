/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var API = {
    csw: require('../api/CSW'),
    wms: require('../api/WMS'),
    wmts: require('../api/WMTS')
};

const {addLayer, changeLayerProperties} = require('./layers');

const LayersUtils = require('../utils/LayersUtils');
const {find} = require('lodash');

const RECORD_LIST_LOADED = 'RECORD_LIST_LOADED';
const RESET_CATALOG = 'RESET_CATALOG';
const RECORD_LIST_LOAD_ERROR = 'RECORD_LIST_LOAD_ERROR';
const CHANGE_CATALOG_FORMAT = 'CHANGE_CATALOG_FORMAT';
const ADD_LAYER_ERROR = 'ADD_LAYER_ERROR';
function recordsLoaded(options, result) {
    return {
        type: RECORD_LIST_LOADED,
        searchOptions: options,
        result: result
    };
}

function changeCatalogFormat(format) {
    return {
        type: CHANGE_CATALOG_FORMAT,
        format
    };
}

function resetCatalog() {
    return {
        type: RESET_CATALOG
    };
}

function recordsLoadError(e) {
    return {
        type: RECORD_LIST_LOAD_ERROR,
        error: e
    };
}
function getRecords(format, url, startPosition = 1, maxRecords, filter, options) {
    return (dispatch /* , getState */) => {
        // TODO auth (like) let opts = GeoStoreApi.getAuthOptionsFromState(getState(), {params: {start: 0, limit: 20}, baseURL: geoStoreUrl });
        API[format].getRecords(url, startPosition, maxRecords, filter, options).then((result) => {
            if (result.error) {
                dispatch(recordsLoadError(result));
            } else {
                dispatch(recordsLoaded({
                    url,
                    startPosition,
                    maxRecords,
                    filter
                }, result));
            }
        }).catch((e) => {
            dispatch(recordsLoadError(e));
        });
    };
}
function textSearch(format, url, startPosition, maxRecords, text, options) {
    return (dispatch /* , getState */) => {
        // TODO auth (like) let opts = GeoStoreApi.getAuthOptionsFromState(getState(), {params: {start: 0, limit: 20}, baseURL: geoStoreUrl });
        API[format].textSearch(url, startPosition, maxRecords, text, options).then((result) => {
            if (result.error) {
                dispatch(recordsLoadError(result));
            } else {
                dispatch(recordsLoaded({
                    url,
                    startPosition,
                    maxRecords,
                    text
                }, result));
            }
        }).catch((e) => {
            dispatch(recordsLoadError(e));
        });
    };
}
function addLayerAndDescribe(layer) {
    return (dispatch, getState) => {
        const state = getState();
        const layers = state && state.layers;
        const id = LayersUtils.getLayerId(layer, layers || []);
        dispatch(addLayer({...layer, id}));
        if (layer.type === 'wms') {
            // try to describe layer
            return API.wms.describeLayers(layer.url, layer.name).then((results) => {
                if (results) {
                    let description = find(results, (desc) => desc.name === layer.name );
                    if (description && description.owsType === 'WFS') {
                        dispatch(changeLayerProperties(id, {
                            search: {
                                url: description.owsURL,
                                type: 'wfs'
                            }
                        }));
                    }
                }

            });
        }

    };
}
function addLayerError(error) {
    return {
        type: ADD_LAYER_ERROR,
        error
    };
}

module.exports = {
    RECORD_LIST_LOADED,
    RECORD_LIST_LOAD_ERROR,
    CHANGE_CATALOG_FORMAT,
    ADD_LAYER_ERROR, addLayerError,
    RESET_CATALOG, resetCatalog,
    getRecords,
    textSearch,
    changeCatalogFormat,
    addLayer: addLayerAndDescribe
};
