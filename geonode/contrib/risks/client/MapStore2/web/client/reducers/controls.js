/*
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {TOGGLE_CONTROL, SET_CONTROL_PROPERTY, RESET_CONTROLS} = require('../actions/controls');
const assign = require('object-assign');
/**
 * Manages the state of the controls in MapStore2
 * The root elements of the state returned by this reducers ar variable, but they have
 * this shape
 * ```
 * {
 * [action.control]: {
 *    [action.property]: action.value
 *  }
 *  }
 * }
 * ```
 * where:
 * @prop {string} action.control identifier, used as key
 * @prop {string} action.property the proeprty to set, by default enabled
 * @prop {boolean|string|number|object} action.value the value of the action. If not present is a boolean that toggles
 * @example
 * {
 *   controls: {
 *     help: {
 *       enabled: false
 *     },
 *     print: {
 *       enabled: false
 *     },
 *     toolbar: {
 *       active: null,
 *       expanded: false
 *     },
 *     drawer: {
 *       enabled: false,
 *       menu: '1'
 *     }
 *   }
 * }
 * @memberof reducers
 */
function controls(state = {}, action) {
    switch (action.type) {
        case TOGGLE_CONTROL:
            const property = action.property || 'enabled';
            return assign({}, state, {
                [action.control]: assign({}, state[action.control], {
                    [property]: !(state[action.control] || {})[property]
                })
            });
        case SET_CONTROL_PROPERTY:
            if (action.toggle === true && state[action.control] && state[action.control][action.property] === action.value) {
                return assign({}, state, {
                    [action.control]: assign({}, state[action.control], {
                        [action.property]: undefined
                    })
                });
            }
            return assign({}, state, {
                [action.control]: assign({}, state[action.control], {
                    [action.property]: action.value
                })
            });
        case RESET_CONTROLS: {
            const resetted = Object.keys(state).reduce((previous, controlName) => {
                return assign(previous, {
                    [controlName]: assign({}, state[controlName], state[controlName].enabled === true ? {
                        enabled: false
                    } : {})
                });
            }, {});
            return assign({}, state, resetted);
        }
        default:
            return state;
    }
}

module.exports = controls;
