/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var url = require('url');

var {createStore, compose, applyMiddleware} = require('redux');
var thunkMiddleware = require('redux-thunk');


const urlQuery = url.parse(window.location.href, true).query;
/*eslint-disable */
var warn = console.warn;
/*eslint-enable */

var warningFilterKey = function(warning) {
    // avoid React 0.13.x warning about nested context. Will remove in 0.14
    return warning.indexOf("Warning: owner-based and parent-based contexts differ") >= 0;
};

var DebugUtils = {
    createDebugStore: function(reducer, initialState, userMiddlewares, enhancer) {
        let finalCreateStore;
        if (__DEVTOOLS__ && urlQuery.debug) {
            let logger = require('redux-logger')();
            let immutable = require('redux-immutable-state-invariant')();
            let middlewares = ([immutable, thunkMiddleware, logger]).concat(userMiddlewares || []);
            const {persistState} = require('redux-devtools');
            const DevTools = require('../components/development/DevTools');

            finalCreateStore = compose(
              applyMiddleware.apply(null, middlewares),
              persistState(window.location.href.match(/[?&]debug_session=([^&]+)\b/)),
              window.devToolsExtension ? window.devToolsExtension() : DevTools.instrument()

          )(createStore);
        } else {
            let middlewares = ([thunkMiddleware]).concat(userMiddlewares || []);
            finalCreateStore = applyMiddleware.apply(null, middlewares)(createStore);
        }
        return finalCreateStore(reducer, initialState, enhancer);
    }
};

/*eslint-disable */
console.warn = function() {
    if ( arguments && arguments.length > 0 && typeof arguments[0] === "string" && warningFilterKey(arguments[0]) ) {
        // do not warn
    } else {
        warn.apply(console, arguments);
    }
};
/*eslint-enable */

module.exports = DebugUtils;
