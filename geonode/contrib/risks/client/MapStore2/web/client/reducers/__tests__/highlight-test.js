/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const expect = require('expect');
const highlight = require('../highlight');


describe('Test the highlight reducer', () => {

    it('returns the initial state on unrecognized action', () => {

        const initialState = {
            status: 'disabled',
            layer: 'featureselector',
            features: [],
            highlighted: 0
        };

        let state = highlight(initialState, {type: 'UNKNOWN'});
        expect(state).toBe(initialState);
    });

    it('Change the highlight status', () => {
        let testAction = {
            type: "HIGHLIGHT_STATUS",
            status: "enabled"
        };

        const initialState = {
            status: 'disabled',
            layer: 'featureselector',
            features: [],
            highlighted: 0

        };

        let state = highlight(initialState, testAction);
        expect(state).toExist();

        expect(state.status).toBe("enabled");
        expect(state.layer).toBe("featureselector");
        expect(state.highlighted).toBe(0);
    });

    it('Change the UPDATE_HIGHLIGHTED ', () => {
        let testAction = {
            type: "UPDATE_HIGHLIGHTED",
            features: [0, 1, 2, 3],
            status: 'update'
        };


        let state = highlight( undefined, testAction);
        expect(state).toExist();

        expect(state.status).toBe("update");
        expect(state.layer).toBe("featureselector");
        expect(state.highlighted).toBe(4);
        expect(state.features[1]).toBe(1);

    });
});
