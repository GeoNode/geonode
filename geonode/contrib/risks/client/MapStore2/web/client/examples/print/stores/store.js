/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var DebugUtils = require('../../../utils/DebugUtils');

const {combineReducers} = require('redux');

const map = require('../../../reducers/map');

 // reducers
const allReducers = combineReducers({
    browser: require('../../../reducers/browser'),
    config: require('../../../reducers/config'),
    locale: require('../../../reducers/locale'),
    map: () => {return null; },
    print: require('../../../reducers/print'),
    controls: require('../../../reducers/controls')
});

const rootReducer = (state, action) => {
    let mapState = map(state.map, action);
    return {
        ...allReducers(state, action),
        map: mapState
    };
};

// export the store with the given reducers
module.exports = DebugUtils.createDebugStore(rootReducer, {
    controls: {
        print: {
            enabled: true
        }
    },
    print: {
        spec: {
            antiAliasing: true,
            iconSize: 24,
            legendDpi: 96,
            fontFamily: "Verdana",
            fontSize: 8,
            bold: false,
            italic: false,
            resolution: 96,
            name: '',
            description: ''
        }
    }
});
