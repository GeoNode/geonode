/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const API = require('../WMTS');

describe('Test correctness of the WMTS APIs', () => {
    it('GetRecords', (done) => {
        API.getRecords('base/web/client/test-resources/wmts/GetCapabilities-1.0.0.xml', 0, 1, '').then((result) => {
            try {
                expect(result).toExist();
                expect(result.numberOfRecordsMatched).toBe(3);
                done();
            } catch(ex) {
                done(ex);
            }
        });
    });
});
