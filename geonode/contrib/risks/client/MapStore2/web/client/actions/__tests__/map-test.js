/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var {
    CHANGE_MAP_VIEW,
    CLICK_ON_MAP,
    CHANGE_MOUSE_POINTER,
    CHANGE_ZOOM_LVL,
    CHANGE_MAP_CRS,
    CHANGE_MAP_SCALES,
    CHANGE_MAP_STYLE,
    CHANGE_ROTATION,
    changeMapView,
    clickOnMap,
    changeMousePointer,
    changeZoomLevel,
    changeMapCrs,
    changeMapScales,
    changeMapStyle,
    changeRotation
} = require('../map');

describe('Test correctness of the map actions', () => {

    it('changeMapView', () => {
        const testCenter = 0;
        const testZoom = 3;
        const testBbox = 6;
        const testSize = 9;
        const testProjection = 'EPSG:32632';
        var retval = changeMapView(testCenter, testZoom, testBbox, testSize, null, testProjection);

        expect(retval).toExist();
        expect(retval.type).toBe(CHANGE_MAP_VIEW);
        expect(retval.center).toBe(testCenter);
        expect(retval.zoom).toBe(testZoom);
        expect(retval.bbox).toBe(testBbox);
        expect(retval.size).toBe(testSize);
        expect(retval.projection).toBe(testProjection);
    });

    it('set a new clicked point', () => {
        const testVal = "val";
        const retval = clickOnMap(testVal);

        expect(retval.type).toBe(CLICK_ON_MAP);
        expect(retval.point).toExist();
        expect(retval.point).toBe(testVal);
    });

    it('set a new mouse pointer', () => {
        const testVal = 'pointer';
        const retval = changeMousePointer(testVal);

        expect(retval).toExist();
        expect(retval.type).toBe(CHANGE_MOUSE_POINTER);
        expect(retval.pointer).toBe(testVal);
    });

    it('changes a new zoom level', () => {
        const testVal = 9;
        const retval = changeZoomLevel(testVal);

        expect(retval).toExist();
        expect(retval.type).toBe(CHANGE_ZOOM_LVL);
        expect(retval.zoom).toBe(testVal);
    });

    it('changes map crs', () => {
        const testVal = 'EPSG:4326';
        const retval = changeMapCrs(testVal);

        expect(retval).toExist();
        expect(retval.type).toBe(CHANGE_MAP_CRS);
        expect(retval.crs).toBe(testVal);
    });

    it('changeMapScales', () => {
        const testScales = [100000, 50000, 25000, 10000, 5000];
        const retval = changeMapScales(testScales);

        expect(retval).toExist();
        expect(retval.type).toBe(CHANGE_MAP_SCALES);
        expect(retval.scales).toEqual(testScales);
    });

    it('changeMapStyle', () => {
        let style = {width: 100};
        let mapStateSource = "test";
        var retval = changeMapStyle(style, mapStateSource);

        expect(retval).toExist();
        expect(retval.type).toBe(CHANGE_MAP_STYLE);
        expect(retval.style).toBe(style);
        expect(retval.mapStateSource).toBe(mapStateSource);
    });

    it('changeRotation', () => {
        let angle = 0.5235987755982989;
        let mapStateSource = "test";
        let retval = changeRotation(angle, mapStateSource);
        expect(retval).toExist();
        expect(retval.type).toEqual(CHANGE_ROTATION);
        expect(retval.rotation).toEqual(angle);
        expect(retval.mapStateSource).toEqual(mapStateSource);
    });
});
