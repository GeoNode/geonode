/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {createSelector} = require('reselect');
const {head} = require('lodash');

const ruleselctor = (state) => state.vectorstyler && state.vectorstyler.rule && head(state.vectorstyler.rules.filter((r) => {return r.id === state.vectorstyler.rule; }));

const symbolselector = createSelector([ruleselctor],
     (rule) => ({
    shapeStyle: rule && rule.symbol || {}
}));

module.exports = {
    ruleselctor,
    symbolselector
};
