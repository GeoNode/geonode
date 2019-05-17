/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var { TASK_STARTED, TASK_SUCCESS, TASK_ERROR } = require('../actions/tasks');
var assign = require('object-assign');

function tasks(state = {}, action) {
    switch (action.type) {
        case TASK_STARTED: {
            return assign({}, state, {
                [action.name]: {
                    running: true
                }
            });
        }
        case TASK_SUCCESS: {
            return assign({}, state, {
                [action.name]: {
                    actionPayload: action.actionPayload,
                    name: action.name,
                    result: action.result,
                    running: false,
                    success: true
                }
            });
        }
        case TASK_ERROR: {
            return assign({}, state, {
                [action.name]: {
                    actionPayload: action.actionPayload,
                    error: action.error,
                    name: action.name,
                    running: false,
                    success: false
                }
            });
        }
        default:
            return state;
    }
}

module.exports = tasks;
