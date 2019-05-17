/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const TOGGLE_GRATICULE = 'TOGGLE_GRATICULE';
const UPDATE_MARKER = 'UPDATE_MARKER';


function toggleGraticule() {
    return {
        type: TOGGLE_GRATICULE
    };
}

function updateMarker(point) {
    return {
        type: UPDATE_MARKER,
        point
    };
}

module.exports = {TOGGLE_GRATICULE, UPDATE_MARKER, toggleGraticule, updateMarker};
