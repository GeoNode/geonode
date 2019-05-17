/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var {MAP_TYPE_CHANGED} = require('../actions/home');

function home(state = {mapType: "leaflet"}, action) {
    switch (action.type) {
        case MAP_TYPE_CHANGED:
            return {mapType: action.mapType};
        default:
            return state;
    }
}

module.exports = home;
