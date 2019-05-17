/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const SET_STYLE_PARAMETER = 'SET_STYLE_PARAMETER';

function setStyleParameter(name, value) {
    return {
        type: SET_STYLE_PARAMETER,
        name,
        value
    };
}

module.exports = {
    SET_STYLE_PARAMETER,
    setStyleParameter
};
