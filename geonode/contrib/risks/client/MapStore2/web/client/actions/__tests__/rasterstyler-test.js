/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const {
    SET_RASTERSTYLE_PARAMETER,
    SET_RASTER_LAYER,
    setRasterStyleParameter,
    setRasterLayer
} = require('../rasterstyler');

describe('Test correctness of the rasterstyle actions', () => {

    it('setRasterStyleParameter', () => {
        const retVal = setRasterStyleParameter('cmp', 'property', 'val');
        expect(retVal).toExist();
        expect(retVal.type).toBe(SET_RASTERSTYLE_PARAMETER);
        expect(retVal.component).toBe('cmp');
        expect(retVal.property).toBe('property');
        expect(retVal.value).toBe('val');
    });
    it('setRasterLayer', () => {
        const retVal = setRasterLayer('layer');
        expect(retVal).toExist();
        expect(retVal.type).toBe(SET_RASTER_LAYER);
        expect(retVal.layer).toBe('layer');
    });
});
