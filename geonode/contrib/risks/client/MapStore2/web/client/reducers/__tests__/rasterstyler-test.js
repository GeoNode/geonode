/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const expect = require('expect');

const rasterstyler = require('../rasterstyler');
const {
    SET_RASTERSTYLE_PARAMETER,
    SET_RASTER_LAYER
} = require('../../actions/rasterstyler');

describe('Test the rasterstyler reducer', () => {
    it('set a rasterstyle parameter', () => {
        const state = rasterstyler(undefined, {
            type: SET_RASTERSTYLE_PARAMETER,
            component: 'testComponent',
            property: 'testProperty',
            value: 'testValue'
        });
        expect(state.testComponent).toExist();
        expect(state.testComponent.testProperty).toExist();
        expect(state.testComponent.testProperty).toBe('testValue');
    });

    it('set a rasterstyle layer', () => {
        const state = rasterstyler(undefined, {
            type: SET_RASTER_LAYER,
            layer: 'testLayer'
        });
        expect(state.layer).toBe('testLayer');
    });

});
