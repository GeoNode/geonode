/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var {
    CHANGE_SNAPSHOT_STATE,
    SNAPSHOT_ERROR,
    SNAPSHOT_READY,
    changeSnapshotState,
    onSnapshotError,
    onSnapshotReady,
    saveImage
} = require('../snapshot');
var FileSaver = require('file-saver');
var originalSaveAs = FileSaver.saveAs;
var testImg = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH4AMLEC8BMwzneAAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDhcAAAAMSURBVAjXY/j//z8ABf4C/tzMWecAAAAASUVORK5CYII=";
describe('Test correctness of the snapshot actions', () => {
    beforeEach((done) => {
        originalSaveAs = FileSaver.saveAs;
        FileSaver.saveAs = () => {};
        setTimeout(done);
    });

    afterEach((done) => {
        FileSaver.saveAs = originalSaveAs;
        setTimeout(done);
    });

    it('change snapshot state', () => {
        const testVal = "val";
        const retval = changeSnapshotState(testVal);

        expect(retval.type).toBe(CHANGE_SNAPSHOT_STATE);
        expect(retval.state).toExist();
        expect(retval.state).toBe(testVal);
    });
    it('snapshot error', () => {
        const testVal = "error";
        const retval = onSnapshotError(testVal);

        expect(retval.type).toBe(SNAPSHOT_ERROR);
        expect(retval.error).toExist();
        expect(retval.error).toBe(testVal);
    });

    it('snapshot ready', () => {
        const snapshot = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASwAAA";
        const width = 20;
        const height = 20;
        const size = 20;
        const act = onSnapshotReady(snapshot, width, height, size);
        expect(act).toExist();
        expect(act.type).toBe(SNAPSHOT_READY);
        expect(act.imgData).toExist();
        expect(act.imgData).toBe(snapshot);
        expect(act.width).toExist();
        expect(act.width).toBe(width);
        expect(act.height).toExist();
        expect(act.height).toBe(height);
        expect(act.size).toExist();
        expect(act.size).toBe(size);
    });
    it('test upload canvas exeption action', () => {
        saveImage(testImg);
    });
});
