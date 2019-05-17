/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');

var locale = require('../locale');


describe('Test the locale reducer', () => {
    it('fills localization data from loaded translation file', () => {
        var state = locale({}, {type: 'CHANGE_LOCALE', messages: {}, locale: 'it-IT'});
        expect(state.current).toExist();
        expect(state.current).toBe('it-IT');
        expect(state.messages).toExist();
    });

    it('creates an error on wrongly translation file', () => {
        var state = locale({}, {type: 'LOCALE_LOAD_ERROR', error: 'error'});
        expect(state.loadingError).toExist();
    });

    it('returns original state on unrecognized action', () => {
        var state = locale(1, {type: 'UNKNOWN'});
        expect(state).toBe(1);
    });
});
