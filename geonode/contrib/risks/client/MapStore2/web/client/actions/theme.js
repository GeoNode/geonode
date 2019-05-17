/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const THEME_SELECTED = 'THEME_SELECTED';


function selectTheme(theme) {
    return {
        type: THEME_SELECTED,
        theme
    };
}
module.exports = {
    THEME_SELECTED,
    selectTheme
};
