/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const {
    ON_SHAPE_CHOOSEN,
    ON_SHAPE_ERROR,
    SHAPE_LOADING,
    UPDATE_SHAPE_BBOX,
    onShapeChoosen,
    onShapeError,
    shapeLoading,
    updateShapeBBox
} = require('../shapefile');

describe('Test correctness of the shapefile actions', () => {

    it('onShapeChoosen', () => {
        const retVal = onShapeChoosen('val');
        expect(retVal).toExist();
        expect(retVal.type).toBe(ON_SHAPE_CHOOSEN);
        expect(retVal.layers).toBe('val');
    });

    it('onShapeError', () => {
        const retVal = onShapeError('error');
        expect(retVal).toExist();
        expect(retVal.type).toBe(ON_SHAPE_ERROR);
        expect(retVal.message).toBe('error');
    });

    it('shapeLoading', () => {
        const retVal = shapeLoading(true);
        expect(retVal).toExist();
        expect(retVal.type).toBe(SHAPE_LOADING);
        expect(retVal.status).toBe(true);
    });

    it('updateShapeBBox', () => {
        const bbox = [0, 0, 0, 0];
        const retVal = updateShapeBBox(bbox);
        expect(retVal).toExist();
        expect(retVal.type).toBe(UPDATE_SHAPE_BBOX);
        expect(retVal.bbox).toBe(bbox);
    });

});
