/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const expect = require('expect');

const print = require('../print');
const {
    SET_PRINT_PARAMETER,
    PRINT_CAPABILITIES_LOADED,
    PRINT_CAPABILITIES_ERROR,
    CONFIGURE_PRINT_MAP,
    CHANGE_PRINT_ZOOM_LEVEL,
    CHANGE_MAP_PRINT_PREVIEW,
    PRINT_SUBMITTING,
    PRINT_CREATED,
    PRINT_ERROR,
    PRINT_CANCEL
} = require('../../actions/print');

describe('Test the print reducer', () => {
    it('set a printing parameter', () => {
        const state = print({spec: {}}, {
            type: SET_PRINT_PARAMETER,
            name: 'param',
            value: 'val'
        });
        expect(state.spec.param).toBe('val');
    });

    it('load capabilities', () => {
        const state = print({capabilities: {}, spec: {}}, {
            type: PRINT_CAPABILITIES_LOADED,
            capabilities: {
                layouts: [{name: 'A4'}],
                dpis: [{value: 96}]
            }
        });
        expect(state.capabilities.layouts.length).toBe(1);
        expect(state.capabilities.dpis.length).toBe(1);
        expect(state.spec.sheet).toBe('A4');
        expect(state.spec.resolution).toBe(96);
    });

    it('load capabilities error', () => {
        const state = print({capabilities: {}, spec: {}}, {
            type: PRINT_CAPABILITIES_ERROR,
            error: 'myerror'
        });
        expect(state.error).toBe('myerror');
    });

    it('configure print map', () => {
        const state = print({capabilities: {}, spec: {}}, {
            type: CONFIGURE_PRINT_MAP,
            center: {x: 1, y: 1},
            zoom: 5,
            scaleZoom: 6,
            scale: 10000,
            layers: [],
            projection: 'EPSG:4326'
        });
        expect(state.map).toExist();
        expect(state.map.center).toExist();
        expect(state.map.center.x).toBe(1);
        expect(state.map.zoom).toBe(5);
        expect(state.map.scale).toBe(10000);
        expect(state.map.layers.length).toBe(0);
        expect(state.map.projection).toBe('EPSG:4326');
    });

    it('change print zoom level', () => {
        const state = print({capabilities: {}, spec: {}, map: {
            zoom: 5,
            scaleZoom: 6
        }}, {
            type: CHANGE_PRINT_ZOOM_LEVEL,
            zoom: 8,
            scale: 10000
        });
        expect(state.map).toExist();
        expect(state.map.zoom).toBe(7);
        expect(state.map.scaleZoom).toBe(8);
    });

    it('change map print preview', () => {
        const state = print({capabilities: {}, spec: {}}, {
            type: CHANGE_MAP_PRINT_PREVIEW,
            size: 1000
        });
        expect(state.map).toExist();
        expect(state.map.size).toBe(1000);
    });

    it('print submitting', () => {
        const state = print({capabilities: {}, spec: {}}, {
            type: PRINT_SUBMITTING
        });
        expect(state.isLoading).toBe(true);
    });
    it('print created', () => {
        const state = print({capabilities: {}, spec: {}, isLoading: true}, {
            type: PRINT_CREATED,
            url: 'myurl'
        });
        expect(state.isLoading).toBe(false);
        expect(state.pdfUrl).toBe('myurl');
    });

    it('print error', () => {
        const state = print({capabilities: {}, spec: {}, isLoading: true}, {
            type: PRINT_ERROR,
            error: 'error'
        });
        expect(state.isLoading).toBe(false);
        expect(state.error).toBe('error');
    });

    it('print cancel', () => {
        const state = print({capabilities: {}, spec: {}, pdfUrl: 'myurl'}, {
            type: PRINT_CANCEL
        });
        expect(state.pdfUrl).toNotExist();
    });
});
