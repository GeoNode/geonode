/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var {
    CHANGE_MOUSE_POSITION,
    CHANGE_MOUSE_POSITION_CRS,
    CHANGE_MOUSE_POSITION_STATE,
    changeMousePosition,
    changeMousePositionCrs,
    changeMousePositionState
} = require('../mousePosition');

describe('Test correctness of mausePosition actions', () => {

    it('Test changeMousePosition action creator', () => {
        const position = {lat: 43.5, lng: 11.26};

        var retval = changeMousePosition(position);

        expect(retval).toExist();
        expect(retval.type).toBe(CHANGE_MOUSE_POSITION);
        expect(retval.position).toExist();
        expect(retval.position).toBe(position);
    });

    it('Test changeMousePositionCrs action creator', () => {
        const crs = 'EPSG:4326';

        var retval = changeMousePositionCrs(crs);

        expect(retval).toExist();
        expect(retval.type).toBe(CHANGE_MOUSE_POSITION_CRS);
        expect(retval.crs).toExist();
        expect(retval.crs).toBe(crs);
    });


    it('Test changeMousePositionState action creator', () => {
        const enabled = true;

        var retval = changeMousePositionState(enabled);

        expect(retval).toExist();
        expect(retval.type).toBe(CHANGE_MOUSE_POSITION_STATE);
        expect(retval.enabled).toExist();
        expect(retval.enabled).toBe(true);
    });

});
