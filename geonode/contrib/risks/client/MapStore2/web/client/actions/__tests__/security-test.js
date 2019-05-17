/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var {
    RESET_ERROR,
    resetError
} = require('../security');

describe('Test correctness of the close actions', () => {
    it('resetError', () => {
        var retval = resetError();
        expect(retval).toExist();
        expect(retval.type).toBe(RESET_ERROR);
    });
});
