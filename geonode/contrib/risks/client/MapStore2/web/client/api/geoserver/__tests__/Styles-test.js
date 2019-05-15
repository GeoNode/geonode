/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var API = require('../Styles');

describe('Test styles rest API', () => {
    it('save style', (done) => {
        const STYLE_NAME = "test_TEST_LAYER_1";
        API.saveStyle("base/web/client/test-resources/geoserver/rest/", STYLE_NAME, "STYLE_BODY").then((response)=> {
            expect(response).toExist();
            done();
        });
    });
});
