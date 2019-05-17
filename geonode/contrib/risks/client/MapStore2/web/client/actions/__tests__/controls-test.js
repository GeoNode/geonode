/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var {
    TOGGLE_CONTROL,
    SET_CONTROL_PROPERTY,
    toggleControl,
    setControlProperty
} = require('../controls');

describe('Test correctness of the controls actions', () => {

    it('toggleControl', () => {
        const testControl = 'test';
        var retval = toggleControl(testControl);

        expect(retval).toExist();
        expect(retval.type).toBe(TOGGLE_CONTROL);
        expect(retval.control).toBe(testControl);
        expect(retval.property).toNotExist();
    });

    it('toggleControl with custom property', () => {
        const testControl = 'test';
        const testProperty = 'prop';
        var retval = toggleControl(testControl, testProperty);

        expect(retval).toExist();
        expect(retval.type).toBe(TOGGLE_CONTROL);
        expect(retval.control).toBe(testControl);
        expect(retval.property).toBe(testProperty);
    });

    it('setControlProperty', () => {
        const testControl = 'test';
        const testProperty = 'prop';
        const testValue = 'val';
        var retval = setControlProperty(testControl, testProperty, testValue);

        expect(retval).toExist();
        expect(retval.type).toBe(SET_CONTROL_PROPERTY);
        expect(retval.control).toBe(testControl);
        expect(retval.property).toBe(testProperty);
        expect(retval.value).toBe(testValue);
    });
});
