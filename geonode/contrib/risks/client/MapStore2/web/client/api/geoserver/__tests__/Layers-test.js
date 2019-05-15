/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var API = require('../Layers');

describe('Test layers rest API', () => {
    it('get layer', (done) => {
        const LAYER_NAME = "TEST_LAYER_1";
        API.getLayer("base/web/client/test-resources/geoserver/rest/", LAYER_NAME).then((layer)=> {
            expect(layer).toExist();
            expect(layer.name).toBe(LAYER_NAME);
            done();
        });
    });
});
