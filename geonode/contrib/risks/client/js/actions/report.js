/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const REPORT_MAP_READY = 'REPORT_MAP_READY';
const GENERATE_REPORT = 'GENERATE_REPORT';
const GENERATE_MAP = 'GENERATE_MAP';
const GENERATE_MAP_ERROR = 'GENERATE_MAP_ERROR';
const GENERATE_REPORT_ERROR = 'GENERATE_REPORT_ERROR';
const REPORT_READY = 'REPORT_READY';
function generateReport() {
    return {
        type: GENERATE_REPORT
    };
}
function generateReportError(e) {
    return {
        type: GENERATE_REPORT_ERROR,
        e
    };
}
function generateMapReport() {
    return {
        type: GENERATE_MAP
    };
}

function reportMapReady(dataUrl) {
    return {
        type: REPORT_MAP_READY,
        dataUrl
    };
}
function generateMapError(e) {
    return {
        type: GENERATE_MAP_ERROR,
        e
    };
}
const reportReady = function() {
    return {
        type: REPORT_READY
    };
};
module.exports = {
    GENERATE_MAP,
    GENERATE_MAP_ERROR,
    GENERATE_REPORT,
    REPORT_MAP_READY,
    GENERATE_REPORT_ERROR,
    REPORT_READY,
    reportReady,
    generateReport,
    generateMapError,
    reportMapReady,
    generateMapReport,
    generateReportError
};
