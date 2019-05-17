/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const {loadMapConfig, loadMapInfo, MAP_CONFIG_LOAD_ERROR, MAP_CONFIG_LOADED} = require('../config');

const loggedGetState = () => ({
    security: {
        authHeader: "Basic dGVzdDp0ZXN0"
    }
});

describe('Test configuration related actions', () => {
    it('does not load a missing configuration file', (done) => {
        loadMapConfig('missingConfig.json')((e) => {
            try {
                expect(e).toExist();
                expect(e.type).toBe(MAP_CONFIG_LOAD_ERROR);
                done();
            } catch(ex) {
                done(ex);
            }
        });
    });

    it('loads an existing configuration file', (done) => {
        loadMapConfig('base/web/client/test-resources/testConfig.json', loggedGetState)((e) => {
            try {
                expect(e).toExist();
                expect(e.type).toBe(MAP_CONFIG_LOADED);
                done();
            } catch(ex) {
                done(ex);
            }
        });
    });

    it('loads an broken configuration file', (done) => {
        loadMapConfig('base/web/client/test-resources/testConfig.broken.json', loggedGetState)((e) => {
            try {
                expect(e).toExist();
                expect(e.type).toBe('MAP_CONFIG_LOAD_ERROR');
                done();
            } catch(ex) {
                done(ex);
            }
        });
    });
    it('getResource access info', (done) => {
        loadMapInfo('base/web/client/test-resources/geostore/ShortResource.json', 1)((actionCreator) => {
            try {
                switch (actionCreator.type) {
                    case "MAP_INFO_LOAD_START":
                        expect(actionCreator.mapId).toBe(1);
                        break;
                    case "MAP_INFO_LOADED":
                        let resourceInfo = actionCreator.info;
                        expect(resourceInfo).toExist();
                        expect(resourceInfo.canEdit).toExist();
                        expect(resourceInfo.id).toBe(1);
                        done();
                        break;
                    default:
                        done("ERROR");
                        break;
                }

            } catch(ex) {
                done(ex);
            }
        });
    });
});
