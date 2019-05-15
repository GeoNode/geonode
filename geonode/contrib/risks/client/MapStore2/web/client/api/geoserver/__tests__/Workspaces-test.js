/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var API = require('../Workspaces');

describe('Test Workspaces rest API', () => {
    it('getWorkspaces', (done) => {
        API.getWorkspaces("base/web/client/test-resources/geoserver/rest/").then((workspaces)=> {
            expect(workspaces).toExist();
            done();
        });
    });
    it('saveDatastore', (done) => {
        API.createDataStore("base/web/client/test-resources/geoserver/rest/", "test", "STYLE_BODY").then((response)=> {
            expect(response).toExist();
            done();
        });
    });
});
