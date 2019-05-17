/*
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const TOGGLE_CONTROL = 'TOGGLE_CONTROL';
const SET_CONTROL_PROPERTY = 'SET_CONTROL_PROPERTY';
const RESET_CONTROLS = 'RESET_CONTROLS';

/**
 * Toggle a control property
 * @memberof actions.controls
 * @param  {string} control  the name of the control
 * @param  {boolean|number|string|object} [property] the property to override
 * @return {object} action of type `TOGGLE_CONTROL`, control, and property
 */
function toggleControl(control, property) {
    return {
        type: TOGGLE_CONTROL,
        control,
        property
    };
}

/**
 * Sets a property in a more detailed way
 * @memberof actions.controls
 * @param {string} control  control name
 * @param {string} property the property to set
 * @param {string|number|boolean|object} value the value to set or to check for toggling
 * @param {boolean} [toggle]  if true, the reducer will toggle the property of the control only if is equal to the value parameter
 * @return {object} of type `SET_CONTROL_PROPERTY` with control, property, value and toggle params
 */
function setControlProperty(control, property, value, toggle) {
    return {
        type: SET_CONTROL_PROPERTY,
        control,
        property,
        value,
        toggle
    };
}

/**
 * reset all the controls
 * @memberof actions.controls
 * @return {object} action of type `RESET_CONTROLS`
 */
function resetControls() {
    return {
        type: RESET_CONTROLS
    };
}
/**
 * Actions for controls. Provide a simple generic functionality to toggle a generic
 * control property.
 * @name actions.controls
 */
module.exports = {TOGGLE_CONTROL, SET_CONTROL_PROPERTY, RESET_CONTROLS,
    toggleControl, setControlProperty, resetControls};
