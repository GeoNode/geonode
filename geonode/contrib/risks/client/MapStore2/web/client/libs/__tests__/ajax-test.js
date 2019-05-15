/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var axios = require('../ajax');
const SecurityUtils = require('../../utils/SecurityUtils');
const assign = require('object-assign');

const userA = {
    User: {
        enabled: true,
        groups: "",
        id: 6,
        name: "adminA",
        role: "ADMIN"
    }
};

const securityInfoA = {
    user: userA
};

const userB = assign({}, userA, {
    name: "adminB",
    attribute: [{
        name: "UUID",
        value: "263c6917-543f-43e3-8e1a-6a0d29952f72"
    }, {
        name: "description",
        value: "admin user"
    }
]});

const securityInfoB = {
    user: userB,
    token: "263c6917-543f-43e3-8e1a-6a0d29952f72",
    authHeader: 'Basic 263c6917-543f-43e3-8e1a-6a0d29952f72'
};

const authenticationRules = [
    {
      "urlPattern": ".*geoserver.*",
      "method": "authkey"
    },
    {
      "urlPattern": ".*not-supported.*",
      "method": "not-supported"
    },
    {
      "urlPattern": ".*some-site.*",
      "method": "basic"
    }
];

describe('Tests ajax library', () => {
    it('uses proxy for requests not on the same origin', (done) => {
        axios.get('http://fakeexternaldomain.mapstore2').then(() => {
            done();
        }).catch(ex => {
            expect(ex.config).toExist();
            expect(ex.config.url).toExist();
            expect(ex.config.url).toContain('proxy/?url=');
            done();
        });
    });

    it('does not use proxy for requests on the same origin', (done) => {
        axios.get('base/web/client/test-resources/testConfig.json').then((response) => {
            expect(response.config).toExist();
            expect(response.config.url).toExist();
            expect(response.config.url).toBe('base/web/client/test-resources/testConfig.json');
            done();
        }).catch(ex => {
            done(ex);
        });
    });

    it('uses a custom proxy for requests on the same origin with varius query params', (done) => {
        axios.get('http://fakeexternaldomain.mapstore2', {
            proxyUrl: '/proxy/?url=',
            params: {
                param1: 'param1',
                param2: '',
                param3: undefined,
                param4: null,
                param5: [],
                param6: [1, 2, "3", ''],
                param7: {},
                param8: {
                    a: 'a'
                },
                param9: new Date()
            }})
            .then(() => {
                done();
            })
            .catch((ex) => {
                expect(ex.config).toExist();
                expect(ex.config.url).toExist();
                expect(ex.config.url).toContain('proxy/?url=');
                done();
            });
    });

    it('uses a custom proxy for requests on the same origin with string query param', (done) => {
        axios.get('http://fakeexternaldomain.mapstore2', {
                proxyUrl: '/proxy/?url=',
                params: "params"
            })
            .then(() => {
                done();
            })
            .catch((ex) => {
                expect(ex.config).toExist();
                expect(ex.config.url).toExist();
                expect(ex.config.url).toContain('proxy/?url=');
                done();
            });
    });

    it('does not use proxy for requests to CORS enabled urls', (done) => {
        axios.get('http://www.google.com', {
            timeout: 1,
            proxyUrl: {
                url: '/proxy/?url=',
                useCORS: ['http://www.google.com']
            }
        }).then(() => {
            done();
        }).catch((ex) => {
            expect(ex.code).toBe("ECONNABORTED");
            done();
        });
    });

    it('does use proxy for requests on not CORS enabled urls', (done) => {
        axios.get('http://notcors.mapstore2', {
            proxyUrl: {
                url: '/proxy/?url=',
                useCORS: ['http://cors.mapstore2']
            }
        }).then(() => {
            done();
        }).catch((ex) => {
            expect(ex.config).toExist();
            expect(ex.config.url).toExist();
            expect(ex.config.url).toContain('proxy/?url=');
            done();
        });
    });

    it('test add authkey authentication to axios config with no login', (done) => {
        // mocking the authentication rules
        expect.spyOn(SecurityUtils, 'isAuthenticationActivated').andReturn(true);
        expect.spyOn(SecurityUtils, 'getAuthenticationRules').andReturn(authenticationRules);
        expect(SecurityUtils.getAuthenticationRules().length).toBe(3);
        // authkey authentication with no user
        expect.spyOn(SecurityUtils, 'getSecurityInfo').andReturn(null);
        axios.get('http://www.some-site.com/geoserver?parameter1=value1&parameter2=value2').then(() => {
            done();
        }).catch((exception) => {
            expect(exception.config).toExist();
            expect(exception.config.url).toExist();
            expect(exception.config.url.indexOf('authkey')).toBeLessThan(0);
            done();
        });
    });

    it('test add authkey authentication to axios config with login but no uuid', (done) => {
        // mocking the authentication rules
        expect.spyOn(SecurityUtils, 'isAuthenticationActivated').andReturn(true);
        expect.spyOn(SecurityUtils, 'getAuthenticationRules').andReturn(authenticationRules);
        expect(SecurityUtils.getAuthenticationRules().length).toBe(3);
        // authkey authentication with user but no uuid
        expect.spyOn(SecurityUtils, 'getSecurityInfo').andReturn(securityInfoA);
        axios.get('http://www.some-site.com/geoserver?parameter1=value1&parameter2=value2').then(() => {
            done();
        }).catch((exception) => {
            expect(exception.config).toExist();
            expect(exception.config.url).toExist();
            expect(exception.config.url.indexOf('authkey')).toBeLessThan(0);
            done();
        });
    });

    it('test add authkey authentication to axios config with login and uuid', (done) => {
        // mocking the authentication rules
        expect.spyOn(SecurityUtils, 'isAuthenticationActivated').andReturn(true);
        expect.spyOn(SecurityUtils, 'getAuthenticationRules').andReturn(authenticationRules);
        expect(SecurityUtils.getAuthenticationRules().length).toBe(3);
        // authkey authentication with user
        expect.spyOn(SecurityUtils, 'getSecurityInfo').andReturn(securityInfoB);
        axios.get('http://www.some-site.com/geoserver?parameter1=value1&parameter2=value2').then(() => {
            done();
        }).catch((exception) => {
            expect(exception.config).toExist();
            expect(exception.config.url).toExist();
            expect(exception.config.url.indexOf('authkey')).toBeGreaterThan(-1);
            done();
        });
    });

    it('test add authkey authentication to axios config with login and uuid but authentication deactivated', (done) => {
        // mocking the authentication rules
        expect.spyOn(SecurityUtils, 'isAuthenticationActivated').andReturn(false);
        expect.spyOn(SecurityUtils, 'getAuthenticationRules').andReturn(authenticationRules);
        expect(SecurityUtils.getAuthenticationRules().length).toBe(3);
        // authkey authentication with user
        expect.spyOn(SecurityUtils, 'getSecurityInfo').andReturn(securityInfoB);
        axios.get('http://www.some-site.com/geoserver?parameter1=value1&parameter2=value2').then(() => {
            done();
        }).catch((exception) => {
            expect(exception.config).toExist();
            expect(exception.config.url).toExist();
            expect(exception.config.url.indexOf('authkey')).toBeLessThan(0);
            done();
        });
    });

    it('test add basic authentication to axios config', (done) => {
        // mocking the authentication rules
        expect.spyOn(SecurityUtils, 'isAuthenticationActivated').andReturn(true);
        expect.spyOn(SecurityUtils, 'getAuthenticationRules').andReturn(authenticationRules);
        expect(SecurityUtils.getAuthenticationRules().length).toBe(3);
        // basic authentication header available
        expect.spyOn(SecurityUtils, 'getSecurityInfo').andReturn(securityInfoB);
        axios.get('http://www.some-site.com/index?parameter1=value1&parameter2=value2').then(() => {
            done();
        }).catch((exception) => {
            expect(exception.config).toExist();
            expect(exception.config.headers).toExist();
            expect(exception.config.headers.Authorization).toBe('Basic 263c6917-543f-43e3-8e1a-6a0d29952f72');
            done();
        });
    });
});
