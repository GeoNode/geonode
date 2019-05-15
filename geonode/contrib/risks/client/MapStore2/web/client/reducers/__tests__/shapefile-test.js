/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const expect = require('expect');

const shapefile = require('../shapefile');
const {
    ON_SHAPE_CHOOSEN,
    ON_SHAPE_ERROR,
    SHAPE_LOADING,
    UPDATE_SHAPE_BBOX
} = require('../../actions/shapefile');

describe('Test the shapefile reducer', () => {
    it('shapefile defaults', () => {
        const state = shapefile(undefined, {
            type: ''
        });
        expect(state.layers).toBe(null);
        expect(state.error).toBe(null);
        expect(state.loading).toBe(false);

    });
    it('shapefile choosen', () => {
        const state = shapefile(undefined, {
            type: ON_SHAPE_CHOOSEN,
            layers: 'test'
        });
        expect(state.layers).toBe('test');
    });

    it('shapefile error', () => {
        const state = shapefile(undefined, {
            type: ON_SHAPE_ERROR,
            message: 'error'
        });
        expect(state.error).toBe('error');
    });

    it('shapefile loading', () => {
        const state = shapefile(undefined, {
            type: SHAPE_LOADING,
            status: true
        });
        expect(state.loading).toBe(true);
    });

    it('shapefile updateShapeBBox', () => {
        const bbox = [0, 0, 0, 0];
        const state = shapefile(undefined, {
            type: UPDATE_SHAPE_BBOX,
            bbox: bbox
        });
        expect(state.bbox).toBe(bbox);
    });
});
