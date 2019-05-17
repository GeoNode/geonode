/**
 * Copyright 2015-2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const disaster = require('../disaster');
const {
    DATA_LOADING,
    DATA_LOADED,
    DATA_ERROR,
    TOGGLE_DIM
} = require('../../actions/disaster');

require('babel-polyfill');

describe('Test the disaster reducer', () => {
    const appState = {dim: {dim1: 0, dim2: 1}, loading: false, error: null, data: null};

    it('returns original state on unrecognized action', () => {
        const state = disaster(appState, {type: 'UNKNOWN'});
        expect(state).toEqual(appState);
    });
    it('test toggledim action', () => {
        const testAction = {
            type: TOGGLE_DIM
        };
        const state = disaster( appState, testAction);
        expect(state.dim.dim1).toBe(1);
    });
    it('test loading action', () => {
        const testAction = {
            type: DATA_LOADING
        };
        const state = disaster( appState, testAction);
        expect(state.loading).toBeTruthy();
    });
    it('test loading error ', () => {
        const loadingAction = {
           type: DATA_LOADING
        };
        const errorAction = {
            type: DATA_ERROR,
            error: {message: "error"}
        };
        const loadingState = disaster( appState, loadingAction);
        const errorState = disaster(loadingState, errorAction);
        expect(errorState.error).toExist();
        expect(errorState.error).toEqual(errorAction.error);
        expect(errorState.loading).toBeFalsy();
        expect(errorState.data).toBe(null);
    });
    it('test data loaded', () => {
        const loadingAction = {
           type: DATA_LOADING
        };
        const dataAction = {
            type: DATA_LOADED,
            data: {test: true}
        };
        const loadingState = disaster( appState, loadingAction);
        const dataState = disaster(loadingState, dataAction);
        expect(dataState.error).toBe(null);
        expect(dataState.loading).toBeFalsy();
        expect(dataState.test).toBeTruthy();
    });

});
