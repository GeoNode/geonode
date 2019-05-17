/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const assign = require('object-assign');
const {
     GENERATE_REPORT,
     GENERATE_MAP,
     REPORT_MAP_READY,
     REPORT_READY,
     GENERATE_REPORT_ERROR,
     GENERATE_MAP_ERROR
 } = require('../actions/report');

function report(state = {}, action) {
    switch (action.type) {
        case GENERATE_REPORT: {
            return assign({}, state, {processing: true, mapImg: undefined, chartImg: undefined});
        }
        case GENERATE_REPORT_ERROR: {
            return assign({}, state, {processing: false, mapImg: undefined, chartImg: undefined, generateMap: false});
        }
        case GENERATE_MAP: {
            return assign({}, state, {generateMap: true, mapImg: undefined});
        }
        case GENERATE_MAP_ERROR: {
            return assign({}, state, {generateMap: false, mapImg: undefined, processing: false});
        }
        case REPORT_MAP_READY: {
            return assign({}, state, {generateMap: false, mapImg: action.dataUrl});
        }
        case REPORT_READY: {
            return assign({}, state, {generateMap: false, mapImg: undefined, processing: false});
        }
        default:
             return state;
    }
}

module.exports = report;

