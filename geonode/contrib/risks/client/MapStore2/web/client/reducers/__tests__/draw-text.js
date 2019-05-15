/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const expect = require('expect');
const draw = require('../draw');


describe('Test the draw reducer', () => {

    it('returns the initial state on unrecognized action', () => {

        const initialState = {
            drawStatus: null,
            drawOwner: null,
            drawMethod: null,
            features: []
        };

        let state = draw(initialState, {type: 'UNKNOWN'});
        expect(state).toBe(initialState);
    });

    it('Change the drawing status', () => {
        let testAction = {
            type: "CHANGE_DRAWING_STATUS",
            status: "start",
            method: "Circle",
            owner: "queryform",
            features: []
        };

        let initialState = {
            drawStatus: null,
            drawOwner: null,
            drawMethod: null,
            features: []
        };

        let state = draw(initialState, testAction);
        expect(state).toExist();

        expect(state.drawStatus).toBe("start");
        expect(state.drawOwner).toBe("queryform");
        expect(state.drawMethod).toBe("Circle");
        expect(state.features.length).toBe(0);
    });
});
