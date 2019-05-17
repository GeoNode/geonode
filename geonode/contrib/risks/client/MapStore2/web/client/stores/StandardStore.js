/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const assign = require('object-assign');

const {mapConfigHistory, createHistory} = require('../utils/MapHistoryUtils');

const map = mapConfigHistory(require('../reducers/map'));

const layers = require('../reducers/layers');
const mapConfig = require('../reducers/config');

const DebugUtils = require('../utils/DebugUtils');
const {compose} = require('redux');
const {combineReducers, combineEpics} = require('../utils/PluginsUtils');

const LayersUtils = require('../utils/LayersUtils');
const {CHANGE_BROWSER_PROPERTIES} = require('../actions/browser');
const {persistStore, autoRehydrate} = require('redux-persist');
const {createEpicMiddleware} = require('redux-observable');

const SecurityUtils = require('../utils/SecurityUtils');
const ListenerEnhancer = require('@carnesen/redux-add-action-listener-enhancer').default;

module.exports = (initialState = {defaultState: {}, mobile: {}}, appReducers = {}, appEpics = {}, plugins, storeOpts) => {
    const allReducers = combineReducers(plugins, {
        ...appReducers,
        localConfig: require('../reducers/localConfig'),
        locale: require('../reducers/locale'),
        browser: require('../reducers/browser'),
        controls: require('../reducers/controls'),
        theme: require('../reducers/theme'),
        help: require('../reducers/help'),
        map: () => {return null; },
        mapInitialConfig: () => {return null; },
        layers: () => {return null; }
    });
    const rootEpic = combineEpics(plugins, appEpics);
    const defaultState = initialState.defaultState;
    const mobileOverride = initialState.mobile;
    const epicMiddleware = createEpicMiddleware(rootEpic);
    const rootReducer = (state, action) => {
        let mapState = createHistory(LayersUtils.splitMapAndLayers(mapConfig(state, action)));
        let newState = {
            ...allReducers(state, action),
            map: mapState && mapState.map ? map(mapState.map, action) : null,
            mapInitialConfig: (mapState && mapState.mapInitialConfig) || (mapState && mapState.loadingError && {
                loadingError: mapState.loadingError
            }) || null,
            layers: mapState ? layers(mapState.layers, action) : null
        };
        if (action && action.type === CHANGE_BROWSER_PROPERTIES && newState.browser.mobile) {
            newState = assign(newState, mobileOverride);
        }

        return newState;
    };
    let store;
    let enhancer;
    if (storeOpts && storeOpts.persist) {
        enhancer = autoRehydrate();
    }
    if (storeOpts && storeOpts.notify) {
        enhancer = enhancer ? compose(enhancer, ListenerEnhancer) : ListenerEnhancer;
    }
    store = DebugUtils.createDebugStore(rootReducer, defaultState, [epicMiddleware], enhancer);
    if (storeOpts && storeOpts.persist) {
        persistStore(store, storeOpts.persist, storeOpts.onPersist);
    }
    SecurityUtils.setStore(store);
    return store;
};
