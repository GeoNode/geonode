/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var {changeBrowserProperties, CHANGE_BROWSER_PROPERTIES} = require('../browser');

describe('Test browser related actions', () => {
    it('test browser properties change action', (done) => {
        let e = changeBrowserProperties({touch: true});

        try {
            expect(e).toExist();
            expect(e.type).toBe(CHANGE_BROWSER_PROPERTIES);
            expect(e.newProperties).toExist();
            expect(e.newProperties.touch).toBe(true);
            done();
        } catch(ex) {
            done(ex);
        }
    });
});
