/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const MAP_TYPE_CHANGED = 'MAP_TYPE_CHANGED';

function changeMapType(mapType) {
    return {
        type: MAP_TYPE_CHANGED,
        mapType
    };
}

module.exports = {MAP_TYPE_CHANGED, changeMapType};
