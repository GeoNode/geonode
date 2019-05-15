/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const FEATURE_TYPE_SELECTED = 'FEATURE_TYPE_SELECTED';
const FEATURE_TYPE_LOADED = 'FEATURE_TYPE_LOADED';
const FEATURE_LOADED = 'FEATURE_LOADED';
const FEATURE_TYPE_ERROR = 'FEATURE_TYPE_ERROR';
const FEATURE_ERROR = 'FEATURE_ERROR';
const FEATURE_CLOSE = 'FEATURE_CLOSE';
const QUERY_CREATE = 'QUERY_CREATE';
const QUERY_RESULT = 'QUERY_RESULT';
const QUERY_ERROR = 'QUERY_ERROR';
const RESET_QUERY = 'RESET_QUERY';

const axios = require('../libs/ajax');
const {toggleControl, setControlProperty} = require('./controls');
const FilterUtils = require('../utils/FilterUtils');
const {reset} = require('./queryform');

function featureTypeSelected(url, typeName) {
    return {
        type: FEATURE_TYPE_SELECTED,
        url,
        typeName
    };
}
function featureTypeLoaded(typeName, featureType) {
    return {
        type: FEATURE_TYPE_LOADED,
        typeName,
        featureType
    };
}

function featureTypeError(typeName, error) {
    return {
        type: FEATURE_TYPE_ERROR,
        typeName,
        error
    };
}

function featureLoaded(typeName, feature) {
    return {
        type: FEATURE_LOADED,
        typeName,
        feature
    };
}

function featureError(typeName, error) {
    return {
        type: FEATURE_ERROR,
        typeName,
        error
    };
}

function querySearchResponse(result, searchUrl, filterObj) {
    return {
        type: QUERY_RESULT,
        searchUrl,
        filterObj,
        result
    };
}

function queryError(error) {
    return {
        type: QUERY_ERROR,
        error
    };
}

function describeFeatureType(baseUrl, typeName) {
    return (dispatch) => {
        return axios.get(baseUrl + '?service=WFS&version=1.1.0&request=DescribeFeatureType&typeName=' + typeName + '&outputFormat=application/json').then((response) => {
            if (typeof response.data === 'object') {
                dispatch(featureTypeLoaded(typeName, response.data));
            } else {
                try {
                    JSON.parse(response.data);
                } catch(e) {
                    dispatch(featureTypeError(typeName, 'Error from WFS: ' + e.message));
                }

            }

        }).catch((e) => {
            dispatch(featureTypeError(typeName, e));
        });
    };
}

function loadFeature(baseUrl, typeName) {
    return (dispatch) => {
        return axios.get(baseUrl + '?service=WFS&version=1.1.0&request=GetFeature&typeName=' + typeName + '&outputFormat=application/json').then((response) => {
            if (typeof response.data === 'object') {
                dispatch(featureLoaded(typeName, response.data));
            } else {
                try {
                    JSON.parse(response.data);
                } catch(e) {
                    dispatch(featureError(typeName, 'Error from WFS: ' + e.message));
                }

            }

        }).catch((e) => {
            dispatch(featureError(typeName, e));
        });
    };
}
function createQuery(searchUrl, filterObj) {
    return {
        type: QUERY_CREATE,
        searchUrl,
        filterObj
    };
}

function query(searchUrl, filterObj) {
    createQuery(searchUrl, filterObj);
    let data;
    if (typeof filterObj === 'string') {
        data = filterObj;
    } else {
        data = filterObj.filterType === "OGC" ?
            FilterUtils.toOGCFilter(filterObj.featureTypeName, filterObj, filterObj.ogcVersion, filterObj.sortOptions, filterObj.hits) :
            FilterUtils.toCQLFilter(filterObj);
    }
    return (dispatch, getState) => {
        let state = getState();
        if (state.controls && state.controls.queryPanel && state.controls.drawer && state.controls.drawer.enabled && state.query && state.query.open) {
            dispatch(setControlProperty('drawer', 'enabled', false));
            dispatch(setControlProperty('drawer', 'disabled', true));
        }
        return axios.post(searchUrl + '?service=WFS&&outputFormat=json', data, {
          timeout: 60000,
          headers: {'Accept': 'application/json', 'Content-Type': 'application/json'}
        }).then((response) => {
            dispatch(querySearchResponse(response.data, searchUrl, filterObj));
        }).catch((e) => {
            dispatch(queryError(e));
        });
    };
}

function resetQuery() {
    return {
        type: RESET_QUERY
    };
}


function toggleQueryPanel(url, name) {
    return (dispatch, getState) => {
        if (getState().query.typeName !== name) {
            dispatch(reset());
        }
        dispatch(featureTypeSelected(url, name));
        dispatch(toggleControl('queryPanel', null));
        dispatch(setControlProperty('drawer', 'width', getState().controls.queryPanel.enabled ? 700 : 300));
    };
}
function featureClose() {
    return {
        type: FEATURE_CLOSE
    };
}

function closeResponse() {
    return (dispatch, getState) => {
        dispatch(featureClose());
        let state = getState();
        if (state.controls && state.controls.queryPanel && state.controls.drawer && !state.controls.drawer.enabled) {
            dispatch(setControlProperty('drawer', 'enabled', true));
            dispatch(setControlProperty('drawer', 'disabled', false));
        }
    };
}

module.exports = {
    FEATURE_TYPE_SELECTED,
    FEATURE_TYPE_LOADED,
    FEATURE_LOADED,
    FEATURE_TYPE_ERROR,
    FEATURE_ERROR,
    FEATURE_CLOSE,
    QUERY_CREATE,
    QUERY_RESULT,
    QUERY_ERROR,
    RESET_QUERY,
    featureTypeSelected,
    describeFeatureType,
    loadFeature,
    createQuery,
    query,
    featureClose,
    resetQuery,
    toggleQueryPanel,
    closeResponse
};
