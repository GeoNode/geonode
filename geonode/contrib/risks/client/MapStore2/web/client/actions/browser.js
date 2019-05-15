/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const CHANGE_BROWSER_PROPERTIES = 'CHANGE_BROWSER_PROPERTIES';


function changeBrowserProperties(properties) {
    return {
        type: CHANGE_BROWSER_PROPERTIES,
        newProperties: properties
    };
}
module.exports = {CHANGE_BROWSER_PROPERTIES, changeBrowserProperties};
