/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');
var ProxyUtils = require('../ProxyUtils');

describe('ProxyUtils test', () => {
    it('Need Proxy', () => {
        let res = ProxyUtils.needProxy("http:someurl.com");
        expect(res).toBe(true);
    });
    it('GetProxyUrl', () => {
        let res = ProxyUtils.getProxyUrl({proxyUrl: "http:someurl.com"});
        expect(res).toBe("http:someurl.com");
    });
});
