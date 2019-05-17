/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const DATA_LOADING = 'DATA_LOADING';
const DATA_LOADED = 'DATA_LOADED';
const DATA_ERROR = 'DATA_ERROR';
const GET_DATA = 'GET_DATA';
const ANALYSIS_DATA_LOADED = 'ANALYSIS_DATA_LOADED';
const TOGGLE_DIM = 'TOGGLE_DIM';
const SET_DIM_IDX = 'SET_DIM_IDX';
const FEATURES_LOADING = 'FEATURES_LOADING';
const FEATURES_LOADED = 'FEATURES_LOADED';
const FEATURES_ERROR = 'FEATURES_ERROR';
const TOGGLE_ADMIN_UNITS = 'TOGGLE_ADMIN_UNITS';
const LOAD_RISK_MAP_CONFIG = 'LOAD_RISK_MAP_CONFIG';
const GET_RISK_FEATURES = 'GET_RISK_FEATURES';
const GET_ANALYSIS_DATA = 'GET_ANALYSIS_DATA';
const ZOOM_IN_OUT = 'ZOOM_IN_OUT';
const INIT_RISK_APP = 'INIT_RISK_APP';
const GET_S_FURTHER_RESOURCE_DATA = 'GET_S_FURTHER_RESOURCE_DATA';
const SET_CHART_SLIDER_INDEX = 'SET_CHART_SLIDER_INDEX';
const CHART_SLIDER_UPDATE = 'CHART_SLIDER_UPDATE';
const SET_ADDITIONAL_CHART_INDEX = 'SET_ADDITIONAL_CHART_INDEX';
const TOGGLE_SWITCH_CHART = 'TOGGLE_SWITCH_CHART';

function initState({href, geomHref, gc, ac}) {
    return {
        type: INIT_RISK_APP,
        href,
        geomHref,
        gc,
        ac
    };

}

function toggleDim() {
    return {
        type: TOGGLE_DIM
    };
}
function getData(url, cleanState = false) {
    return {
        type: GET_DATA,
        url,
        cleanState
    };
}
function dataLoading() {
    return {
        type: DATA_LOADING
    };
}
function dataLoaded(data, cleanState) {
    return {
        type: DATA_LOADED,
        data,
        cleanState
    };
}
function dataError(error) {
    return {
        type: DATA_ERROR,
        error
    };
}
function getAnalysisData(url) {
    return {
        type: GET_ANALYSIS_DATA,
        url
    };
}
function analysisDataLoaded(data) {
    return {
        type: ANALYSIS_DATA_LOADED,
        data
    };
}
function featuresError(error) {
    return {
        type: FEATURES_ERROR,
        error
    };
}
function featuresLoading() {
    return {
        type: FEATURES_LOADING
    };
}
function featuresLoaded(data) {
    return {
        type: FEATURES_LOADED,
        data
    };
}
function getFeatures(url) {
    return {
        type: 'GET_RISK_FEATURES',
        url
    };
}

function zoomInOut(dataHref, geomHref) {
    return {
        type: ZOOM_IN_OUT,
        dataHref,
        geomHref
    };
}
function loadMapConfig(configName, mapId, featuresUrl) {
    return {
        type: 'LOAD_RISK_MAP_CONFIG',
        configName,
        mapId,
        featuresUrl
    };
}
function setDimIdx(dim, idx) {
    return {
        type: SET_DIM_IDX,
        dim,
        idx
    };
}
function toggleAdminUnit() {
    return {
        type: TOGGLE_ADMIN_UNITS
    };
}

function getSFurtherResourceData(url, uid, title, head) {
    return {
        type: GET_S_FURTHER_RESOURCE_DATA,
        url,
        uid,
        title,
        head
    };
}

function setChartSliderIndex(index, uid) {
    return {
        type: SET_CHART_SLIDER_INDEX,
        index,
        uid
    };
}

function chartSliderUpdate(index, uid) {
    return {
        type: CHART_SLIDER_UPDATE,
        index,
        uid
    };
}

function setAdditionalChartIndex(section, col, table) {
    return {
        type: SET_ADDITIONAL_CHART_INDEX,
        section,
        col,
        table
    };
}

function toggleSwitchChart() {
    return {
        type: TOGGLE_SWITCH_CHART
    };
}

module.exports = {
    DATA_LOADING,
    DATA_LOADED,
    DATA_ERROR,
    ANALYSIS_DATA_LOADED,
    TOGGLE_DIM,
    SET_DIM_IDX,
    TOGGLE_ADMIN_UNITS,
    GET_DATA,
    LOAD_RISK_MAP_CONFIG,
    GET_RISK_FEATURES,
    GET_ANALYSIS_DATA,
    ZOOM_IN_OUT,
    INIT_RISK_APP,
    GET_S_FURTHER_RESOURCE_DATA,
    SET_CHART_SLIDER_INDEX,
    CHART_SLIDER_UPDATE,
    SET_ADDITIONAL_CHART_INDEX,
    TOGGLE_SWITCH_CHART,
    featuresLoaded,
    featuresLoading,
    featuresError,
    dataError,
    dataLoaded,
    dataLoading,
    getData,
    getFeatures,
    getAnalysisData,
    analysisDataLoaded,
    toggleDim,
    zoomInOut,
    loadMapConfig,
    setDimIdx,
    toggleAdminUnit,
    initState,
    getSFurtherResourceData,
    setChartSliderIndex,
    chartSliderUpdate,
    setAdditionalChartIndex,
    toggleSwitchChart
};
