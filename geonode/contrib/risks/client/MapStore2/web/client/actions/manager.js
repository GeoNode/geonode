/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const MANAGER_ITEM_SELECTED = 'MANAGER_ITEM_SELECTED';

function itemSelected(toolId) {
    return {
        type: MANAGER_ITEM_SELECTED,
        toolId
    };
}

module.exports = {
    MANAGER_ITEM_SELECTED, itemSelected
 };
