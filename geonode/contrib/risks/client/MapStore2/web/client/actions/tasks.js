/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const TASK_STARTED = 'TASK_STARTED';
const TASK_SUCCESS = 'TASK_SUCCESS';
const TASK_ERROR = 'TASK_ERROR';

function taskSuccess(result, name, actionPayload) {
    return {
        type: TASK_SUCCESS,
        result,
        name,
        actionPayload
    };
}

function taskStarted(name) {
    return {
        type: TASK_STARTED,
        name
    };
}

function taskError(error, name, actionPayload) {
    return {
        type: TASK_ERROR,
        error,
        name,
        actionPayload
    };
}

function startTask(task, taskPayload, name, actionPayload) {
    return (dispatch) => {
        dispatch(taskStarted(name));
        task(taskPayload, (result) => {
            dispatch(taskSuccess(result, name, actionPayload));
        }, (error) => {
            dispatch(taskError(error, name, actionPayload));
        });
    };
}


module.exports = {TASK_STARTED, TASK_SUCCESS, TASK_ERROR, startTask, taskSuccess, taskError, taskStarted};
