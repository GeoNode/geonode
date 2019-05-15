/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const assign = require('object-assign');
const {
    DATA_LOADING,
    DATA_LOADED,
    DATA_ERROR,
    TOGGLE_DIM,
    ANALYSIS_DATA_LOADED,
    SET_DIM_IDX,
    TOGGLE_ADMIN_UNITS,
    GET_ANALYSIS_DATA,
    SET_CHART_SLIDER_INDEX,
    SET_ADDITIONAL_CHART_INDEX,
    TOGGLE_SWITCH_CHART
} = require('../actions/disaster');

function disaster(state = {dim: {dim1: 0, dim2: 1, dim1Idx: 0, dim2Idx: 0}}, action) {
    switch (action.type) {
        case DATA_LOADING:
            return assign({}, state, {
                loading: true
            });
        case DATA_LOADED: {
            return action.cleanState ? assign({}, {showSubUnit: true, loading: false, error: null, app: state.app}, action.data) : assign({}, {showSubUnit: state.showSubUnit, loading: false, error: null, dim: state.dim, sliders: state.sliders, riskAnalysis: state.riskAnalysis, app: state.app}, action.data);
        }
        case ANALYSIS_DATA_LOADED: {
            return assign({}, state, { loading: false, error: null, riskAnalysis: action.data});
        }
        case TOGGLE_DIM: {
            const newDim = state.dim && {dim1: state.dim.dim2, dim2: state.dim.dim1, dim1Idx: 0, dim2Idx: 0} || {dim1: 1, dim2: 0, dim1Idx: 0, dim2Idx: 0};
            return assign({}, state, {dim: newDim, sliders: {}});
        }
        case TOGGLE_ADMIN_UNITS: {
            return assign({}, state, {showSubUnit: !state.showSubUnit});
        }
        case SET_DIM_IDX: {
            const newDim = assign({dim1: 0, dim2: 1, dim1Idx: 0, dim2Idx: 0}, state.dim, {[action.dim]: action.idx});
            return assign({}, state, {dim: newDim});
        }
        case DATA_ERROR:
            return assign({}, state, {
                error: action.error,
                loading: false
            });
        case GET_ANALYSIS_DATA:
            return assign({}, state, {
                currentAnalysisUrl: action.url
            });
        case SET_CHART_SLIDER_INDEX:
            let sliders = assign({}, state.sliders);
            sliders[action.uid] = action.index;
            return assign({}, state, {
                sliders
            });
        case SET_ADDITIONAL_CHART_INDEX:
            let additionalCharts = {currentSection: action.section, currentCol: action.col, currentTable: action.table};
            return assign({}, state, {
                additionalCharts
            });
        case TOGGLE_SWITCH_CHART: {
            return assign({}, state, {showChart: !state.showChart});
        }
        default:
            return state;
    }
}

module.exports = disaster;
