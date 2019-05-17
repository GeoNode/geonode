/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const expect = require('expect');
const PluginsUtils = require('../PluginsUtils');
const assign = require('object-assign');
const MapSearchPlugin = require('../../plugins/MapSearch');

describe('PluginsUtils', () => {
    beforeEach( () => {

    });
    afterEach((done) => {
        document.body.innerHTML = '';

        setTimeout(done);
    });
    it('combineReducers', () => {
        const P1 = {
            reducers: {
                reducer1: () => {}
            }
        };

        const P2 = {
            reducers: {
                reducer1: (state = {}) => assign({}, state, { A: "A"}),
                reducer2: (state = {}) => state
            }
        };
        const reducers = {
            reducer3: (state = {}) => state
        };
        const spyNo = expect.spyOn(P1.reducers, "reducer1");
        const finalReducer = PluginsUtils.combineReducers([P1, P2], reducers);
        const state = finalReducer();
        expect(state.reducer1).toExist();
        expect(state.reducer1.A).toBe("A");

        // test overriding
        expect(spyNo.calls.length).toBe(0);
    });
    it('getPluginDescriptor', () => {
        const P1 = assign( () => {}, {
            reducers: {
                reducer1: () => {}
            }
        });
        const item = {
            test: "TEST"
        };
        const P2 = assign( () => {}, {
            P1: item,
            reducers: {
                reducer1: () => ({ A: "A"}),
                reducer2: () => {}
            }
        });
        const cfg = {
            test: "TEST"
        };
        let desc1 = PluginsUtils.getPluginDescriptor({}, {P1Plugin: P1, P2Plugin: P2}, [{name: "P1", cfg}, "P2"], "P1" );
        expect(desc1).toExist();
        expect(desc1.id).toBe("P1");
        expect(desc1.name).toBe("P1");
        expect(desc1.cfg).toExist(cfg);
        expect(desc1.items.length).toBe(1);
        expect(desc1.items[0].test).toBe(item.test);
        expect(desc1.items[0].cfg).toExist();

    });
    it('combineEpics', () => {
        const plugins = {MapSearchPlugin: MapSearchPlugin};
        const appEpics = {appEpics: (actions$) => actions$.ofType('TEST_ACTION').map({type: "NEW_ACTION_TEST"})};
        const epics = PluginsUtils.combineEpics(plugins, appEpics);
        expect(typeof epics ).toEqual('function');
    });

});
