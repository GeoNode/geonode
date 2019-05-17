/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const expect = require('expect');

const controls = require('../controls');
const {TOGGLE_CONTROL, SET_CONTROL_PROPERTY, RESET_CONTROLS} = require('../../actions/controls');

describe('Test the constrols reducer', () => {
    it('toggles a control the first time', () => {
        const state = controls({}, {
            type: TOGGLE_CONTROL,
            control: 'mycontrol'
        });
        expect(state.mycontrol).toExist();
        expect(state.mycontrol.enabled).toBe(true);
    });

    it('toggles a control already initialized', () => {
        const state = controls({
            mycontrol: {
                enabled: true
            }
        }, {
            type: TOGGLE_CONTROL,
            control: 'mycontrol'
        });
        expect(state.mycontrol).toExist();
        expect(state.mycontrol.enabled).toBe(false);
    });

    it('toggles a control using custom property', () => {
        const state = controls({
            mycontrol: {
                custom: false
            }
        }, {
            type: TOGGLE_CONTROL,
            control: 'mycontrol',
            property: 'custom'
        });
        expect(state.mycontrol).toExist();
        expect(state.mycontrol.custom).toBe(true);
    });

    it('set a control property', () => {
        const state = controls({}, {
            type: SET_CONTROL_PROPERTY,
            control: 'mycontrol',
            property: 'prop',
            value: 'val'
        });
        expect(state.mycontrol).toExist();
        expect(state.mycontrol.prop).toBe('val');
    });


    it('reset the controls', () => {
        const state = controls(
            {
                c1: { enabled: true},
                c2: { enabled: false},
                c3: { idonthaveenabledfield: "whatever"}
            }, {
            type: RESET_CONTROLS
        });
        expect(state.c1).toExist();
        expect(state.c2).toExist();
        expect(state.c3).toExist();
        expect(state.c1.enabled).toBe(false);
        expect(state.c2.enabled).toBe(false);
        expect(state.c3.enabled).toNotExist();
    });
});
