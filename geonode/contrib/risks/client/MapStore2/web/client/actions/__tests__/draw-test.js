/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const {
    CHANGE_DRAWING_STATUS,
    END_DRAWING,
    changeDrawingStatus,
    endDrawing
} = require('../draw');

describe('Test correctness of the draw actions', () => {

    it('changeDrawingStatus', () => {
        let status = "start";
        let method = "Circle";
        let owner = "queryform";
        let features = [];

        let retval = changeDrawingStatus(status, method, owner, features);

        expect(retval).toExist();
        expect(retval.type).toBe(CHANGE_DRAWING_STATUS);
        expect(retval.status).toBe("start");
        expect(retval.method).toBe("Circle");
        expect(retval.owner).toBe("queryform");
        expect(retval.features.length).toBe(0);
    });

    it('endDrawing', () => {
        let geometry = "geometry";
        let owner = "queryform";

        let retval = endDrawing(geometry, owner);

        expect(retval).toExist();
        expect(retval.type).toBe(END_DRAWING);
        expect(retval.geometry).toBe("geometry");
        expect(retval.owner).toBe("queryform");
    });
});
