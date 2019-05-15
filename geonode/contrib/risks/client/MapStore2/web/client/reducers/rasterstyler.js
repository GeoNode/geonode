/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {
    SET_RASTERSTYLE_PARAMETER,
    SET_RASTER_LAYER
} = require('../actions/rasterstyler');


const assign = require('object-assign');
const { STYLER_RESET } = require('../actions/styler');

const initialSpec = {
    pseudoband: {band: '1', contrast: 'none', algorithm: "none", gammaValue: 1, min: 1, max: 255},
    redband: {band: '1', contrast: 'none', algorithm: "none", gammaValue: 1, min: 1, max: 255},
    blueband: {band: '3', contrast: 'none', algorithm: "none", gammaValue: 1, min: 1, max: 255},
    greenband: {band: '2', contrast: 'none', algorithm: "none", gammaValue: 1, min: 1, max: 255},
    grayband: {band: '1', contrast: 'none', algorithm: "none", gammaValue: 1, min: 1, max: 255},
    pseudocolor: {colorMapEntry: [], type: 'ramp', selected: null, opacity: '1.00', activepanel: "1"},
    equalinterval: {classes: 6, max: 255, min: 0, ramp: "Blues"}
};

function setBaseOptions(describe = {}) {
    let newInit = {};
    Object.keys(initialSpec).reduce((pr, next) => {
        pr[next] = assign({}, initialSpec[next]);
        return pr;
    }, newInit);
    if (describe.bands && describe.bands.length > 0) {
        newInit.pseudoband.band = describe.bands[0];
        newInit.redband.band = describe.bands[0];
        newInit.greenband.band = describe.bands.length > 1 ? describe.bands[1] : describe.bands[0];
        newInit.blueband.band = describe.bands.length > 2 ? describe.bands[2] : describe.bands[0];
        newInit.grayband.band = describe.bands[0];
    }
    if (describe.range) {
        newInit.equalinterval.min = describe.range.min;
        newInit.equalinterval.max = describe.range.max;
    }
    return newInit;
}

function rasterstyler(state = initialSpec, action) {
    switch (action.type) {
        case SET_RASTERSTYLE_PARAMETER: {
            return assign({}, state, {
                [action.component]: assign({}, state[action.component], {
                    [action.property]: action.value
                })
            });
        }
        case SET_RASTER_LAYER: {

            return assign({}, setBaseOptions(action.layer.describeLayer), { layer: action.layer});
        }
        case STYLER_RESET: {
            return initialSpec;
        }
        default:
            return state;
    }
}

module.exports = rasterstyler;
