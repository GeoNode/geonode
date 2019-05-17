/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

module.exports = {
    pages: [{
        name: "home",
        path: "/",
        component: require('./pages/Home')
    }, {
        name: "main",
        path: "/main",
        component: require('./pages/Main')
    }],
    pluginsDef: require('./plugins.js'),
    initialState: {
        defaultState: {},
        mobile: {}
    }
};
