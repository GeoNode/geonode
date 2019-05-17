/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const {
    PRINT_CAPABILITIES_LOADED,
    PRINT_CAPABILITIES_ERROR,
    SET_PRINT_PARAMETER,
    CONFIGURE_PRINT_MAP,
    CHANGE_PRINT_ZOOM_LEVEL,
    CHANGE_MAP_PRINT_PREVIEW,
    PRINT_SUBMITTING,
    PRINT_CREATED,
    PRINT_ERROR,
    PRINT_CANCEL,
    loadPrintCapabilities,
    setPrintParameter,
    configurePrintMap,
    changePrintZoomLevel,
    changeMapPrintPreview,
    printSubmit,
    printSubmitting,
    printCancel
} = require('../print');

describe('Test correctness of the print actions', () => {

    it('loadPrintCapabilities', (done) => {
        loadPrintCapabilities('base/web/client/test-resources/info.json')((e) => {
            try {
                expect(e).toExist();
                expect(e.type).toBe(PRINT_CAPABILITIES_LOADED);
                done();
            } catch(ex) {
                done(ex);
            }
        });
    });

    it('loadPrintCapabilities error', (done) => {
        loadPrintCapabilities('base/web/client/test-resources/missing.json')((e) => {
            try {
                expect(e).toExist();
                expect(e.type).toBe(PRINT_CAPABILITIES_ERROR);
                done();
            } catch(ex) {
                done(ex);
            }
        });
    });

    it('setPrintParameter', () => {
        const retVal = setPrintParameter('name', 'val');
        expect(retVal).toExist();
        expect(retVal.type).toBe(SET_PRINT_PARAMETER);
        expect(retVal.name).toBe('name');
        expect(retVal.value).toBe('val');
    });

    it('configurePrintMap', () => {
        const retVal = configurePrintMap({x: 1, y: 1}, 5, 6, 2.0, [], 'EPSG:4326');
        expect(retVal).toExist();
        expect(retVal.type).toBe(CONFIGURE_PRINT_MAP);
        expect(retVal.center).toExist();
        expect(retVal.center.x).toBe(1);
        expect(retVal.zoom).toBe(5);
        expect(retVal.scaleZoom).toBe(6);
        expect(retVal.scale).toBe(2.0);
        expect(retVal.layers).toExist();
        expect(retVal.layers.length).toBe(0);
        expect(retVal.projection).toBe('EPSG:4326');
    });

    it('changePrintZoomLevel', () => {
        const retVal = changePrintZoomLevel(5, 10000);
        expect(retVal).toExist();
        expect(retVal.type).toBe(CHANGE_PRINT_ZOOM_LEVEL);
        expect(retVal.zoom).toBe(5);
        expect(retVal.scale).toBe(10000);
    });

    it('changeMapPrintPreview', () => {
        const retVal = changeMapPrintPreview({x: 1, y: 1}, 5, {bounds: {}}, {width: 10, height: 50}, 'source', 'EPSG:4326');
        expect(retVal).toExist();
        expect(retVal.type).toBe(CHANGE_MAP_PRINT_PREVIEW);
        expect(retVal.center).toExist();
        expect(retVal.center.x).toBe(1);
        expect(retVal.zoom).toBe(5);
        expect(retVal.bbox).toExist();
        expect(retVal.bbox.bounds).toExist();
        expect(retVal.size).toExist();
        expect(retVal.size.width).toBe(10);
        expect(retVal.size.height).toBe(50);
        expect(retVal.mapStateSource).toBe('source');
        expect(retVal.projection).toBe('EPSG:4326');
    });

    it('printSubmit', (done) => {
        printSubmit('base/web/client/test-resources/print.json', {})((e) => {
            try {
                expect(e).toExist();
                expect(e.type).toBe(PRINT_CREATED);
                done();
            } catch(ex) {
                done(ex);
            }
        });
    });

    it('printSubmit error', (done) => {
        printSubmit('base/web/client/test-resources/missing.json', {})((e) => {
            try {
                expect(e).toExist();
                expect(e.type).toBe(PRINT_ERROR);
                done();
            } catch(ex) {
                done(ex);
            }
        });
    });

    it('printSubmitting', () => {
        const retVal = printSubmitting();
        expect(retVal).toExist();
        expect(retVal.type).toBe(PRINT_SUBMITTING);
    });

    it('printCancel', () => {
        const retVal = printCancel();
        expect(retVal).toExist();
        expect(retVal.type).toBe(PRINT_CANCEL);
    });
});
