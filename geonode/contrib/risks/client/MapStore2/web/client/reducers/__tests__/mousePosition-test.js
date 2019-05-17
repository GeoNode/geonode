/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');
var mousePosition = require('../mousePosition');

describe('Test the mousePosition reducer', () => {

    it('returns original state on unrecognized action', () => {
        let state = mousePosition(1, {type: 'UNKNOWN'});
        expect(state).toBe(1);
    });

    it('Change MousePosition State', () => {
        let testAction = {
            type: 'CHANGE_MOUSE_POSITION_STATE',
            enabled: true
        };
        let state = mousePosition( {}, testAction);
        expect(state.enabled).toExist();
        expect(state.enabled).toBe(true);
    });

    it('Change MousePosition', () => {
        let testAction = {
            type: 'CHANGE_MOUSE_POSITION',
            position: {lat: 0, lng: -55 }
        };
        let state = mousePosition( {}, testAction);
        expect(state.position).toExist();
        expect(state.position.lat).toBe(0);
        expect(state.position.lng).toBe(-55);
    });


    it('Change MousePosition CRS', () => {
        let testAction = {
            type: 'CHANGE_MOUSE_POSITION_CRS',
            crs: 'EPSG:900911'
        };
        let state = mousePosition( {}, testAction);
        expect(state.crs).toExist();
        expect(state.crs).toBe('EPSG:900911');
    });

});
