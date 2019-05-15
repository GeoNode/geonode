/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');

var {TASK_STARTED, TASK_SUCCESS, TASK_ERROR } = require('../../actions/tasks');
var tasks = require('../tasks');

describe('Test the tasks reducer', () => {

    it('test tasks started', () => {
        let name = 'started';
        let testAction = {
            type: TASK_STARTED,
            name: name
        };
        let state = tasks({}, testAction);
        expect(state).toExist();

        expect(state[name].running).toBe(true);
    });

    it('test tasks success', () => {
        let result = {value: "true"};
        let actionPayload = null;

        let name = 'started';
        let testAction = {
            type: TASK_SUCCESS,
            name,
            result,
            actionPayload
        };
        let state = tasks({}, testAction);
        expect(state[name].name).toBe(name);
        expect(state[name].actionPayload).toBe(actionPayload);
        expect(state[name].result).toBe(result);
    });

    it('test task error', () => {
        let name = 'started';
        let error = {value: "true"};
        let actionPayload = null;

        let testAction = {
            type: TASK_ERROR,
            name: name,
            error,
            actionPayload
        };

        let state = tasks({}, testAction);
        expect(state[name].name).toBe(name);
        expect(state[name].actionPayload).toBe(actionPayload);
        expect(state[name].error).toBe(error);
    });

});
