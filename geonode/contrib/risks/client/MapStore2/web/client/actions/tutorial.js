/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const START_TUTORIAL = 'START_TUTORIAL';
const SETUP_TUTORIAL = 'SETUP_TUTORIAL';
const UPDATE_TUTORIAL = 'UPDATE_TUTORIAL';
const DISABLE_TUTORIAL = 'DISABLE_TUTORIAL';
const RESET_TUTORIAL = 'RESET_TUTORIAL';


function startTutorial() {
    return {
        type: START_TUTORIAL
    };
}

function setupTutorial(steps, style, checkbox, defaultStep) {
    return {
        type: SETUP_TUTORIAL,
        steps,
        style,
        checkbox,
        defaultStep
    };
}

function updateTutorial(tour, steps, error) {
    return {
        type: UPDATE_TUTORIAL,
        tour,
        steps,
        error
    };
}

function disableTutorial() {
    return {
        type: DISABLE_TUTORIAL
    };
}


function resetTutorial() {
    return {
        type: RESET_TUTORIAL
    };
}

module.exports = {
    START_TUTORIAL,
    SETUP_TUTORIAL,
    UPDATE_TUTORIAL,
    DISABLE_TUTORIAL,
    RESET_TUTORIAL,
    startTutorial,
    setupTutorial,
    updateTutorial,
    disableTutorial,
    resetTutorial
};
