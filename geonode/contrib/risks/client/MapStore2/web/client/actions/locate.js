/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const CHANGE_LOCATE_STATE = 'CHANGE_LOCATE_STATE';
const LOCATE_ERROR = 'LOCATE_ERROR';

function changeLocateState(state) {
    return {
        type: CHANGE_LOCATE_STATE,
        state: state
    };
}
function onLocateError(error) {
    return {
        type: LOCATE_ERROR,
        error: error
    };
}
module.exports = {
    CHANGE_LOCATE_STATE,
    LOCATE_ERROR,
    changeLocateState,
    onLocateError
};
