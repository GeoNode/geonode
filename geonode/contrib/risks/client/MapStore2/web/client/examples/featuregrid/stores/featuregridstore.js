/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var DebugUtils = require('../../../utils/DebugUtils');

const {combineReducers} = require('redux');
const exampleData = require('json-loader!../../../test-resources/featureGrid-test-data.json');

 // reducers
const reducers = combineReducers({
    browser: require('../../../reducers/browser'),
    config: require('../../../reducers/config'),
    locale: require('../../../reducers/locale'),
    map: require('../../../reducers/map'),
    draw: require('../../../reducers/draw'),
    featuregrid: require('../../../reducers/featuregrid')
});

// export the store with the given reducers
module.exports = DebugUtils.createDebugStore(reducers, {featuregrid: {jsonlayer: exampleData}});
