/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const DebugUtils = require('../../MapStore2/web/client/utils/DebugUtils');
const {combineReducers} = require('redux');
const {syncHistory, routeReducer} = require('react-router-redux');
const {hashHistory} = require('react-router');
const reduxRouterMiddleware = syncHistory(hashHistory);

const rootReducer = combineReducers({
    browser: require('../../MapStore2/web/client/reducers/browser'),
    config: require('../../MapStore2/web/client/reducers/config'),
    locale: require('../../MapStore2/web/client/reducers/locale'),
    map: require('../../MapStore2/web/client/reducers/map'),
    controls: require('../../MapStore2/web/client/reducers/controls'),
    routing: routeReducer
});

const store = DebugUtils.createDebugStore(rootReducer, {}, [reduxRouterMiddleware]);

// Required for replaying actions from devtools to work
reduxRouterMiddleware.listenForReplays(store);

module.exports = store;
