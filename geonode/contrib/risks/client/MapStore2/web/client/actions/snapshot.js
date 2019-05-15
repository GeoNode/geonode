/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
// const axios = require('axios');
const FileUtils = require('../utils/FileUtils');
const CHANGE_SNAPSHOT_STATE = 'CHANGE_SNAPSHOT_STATE';
const SNAPSHOT_ERROR = 'SNAPSHOT_ERROR';
const SNAPSHOT_READY = 'SNAPSHOT_READY';
const SNAPSHOT_ADD_QUEUE = 'SNAPSHOT_ADD_QUEUE';
const SNAPSHOT_REMOVE_QUEUE = 'SNAPSHOT_REMOVE_QUEUE';
const SAVE_IMAGE = 'SAVE_IMAGE';

function changeSnapshotState(state, tainted) {
    return {
        type: CHANGE_SNAPSHOT_STATE,
        state: state,
        tainted
    };
}
function onSnapshotError(error) {
    return {
        type: SNAPSHOT_ERROR,
        error: error
    };
}
function onSnapshotReady(snapshot, width, height, size) {
    return {
        type: SNAPSHOT_READY,
        imgData: snapshot,
        width: width,
        height: height,
        size: size
    };
}

function onCreateSnapshot(options) {
    return {
        type: SNAPSHOT_ADD_QUEUE,
        options: options
    };
}

function onRemoveSnapshot(options) {
    return {
        type: SNAPSHOT_REMOVE_QUEUE,
        options: options
    };
}
/**
 * Post canvas image to servicebox (IF FILE WRITER DON' WORK')
 *
 * @param canvasData {string} image to post string

function postCanvas(canvasData, serviceUrl) {

    return (dispatch) => {
        // dispatch(newMapInfoRequest(reqId, param));
        axios.post(serviceUrl, {params: canvasData}, {headers: {'Content-Type': 'application/upload'}}).then((response) => {
            if (response.data.exceptions) {
                dispatch(onSnapshotError(response.data.exceptions));
            } else {
                window.location.assign(serviceUrl + "?ID=" + response.data);
            }
        }).catch((e) => {
            dispatch(onSnapshotError(e.status + " " + e.statusText));
        });
    };
}
 */
function saveImage(dataURL) {
    FileUtils.downloadCanvasDataURL(dataURL, "snapshot.png", "image/png");
    return {
        type: SAVE_IMAGE,
        dataURL: dataURL
    };
}

module.exports = {
    CHANGE_SNAPSHOT_STATE,
    SNAPSHOT_ERROR,
    SNAPSHOT_READY,
    SNAPSHOT_ADD_QUEUE,
    SNAPSHOT_REMOVE_QUEUE,
    changeSnapshotState,
    onSnapshotError,
    onSnapshotReady,
    onCreateSnapshot,
    onRemoveSnapshot,
    saveImage
};
