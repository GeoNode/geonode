/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const { LOGIN_SUCCESS, LOGIN_FAIL, LOGOUT, CHANGE_PASSWORD_SUCCESS, RESET_ERROR } = require('../actions/security');
const { USERMANAGER_UPDATE_USER } = require('../actions/users');

const SecurityUtils = require('../utils/SecurityUtils');

const assign = require('object-assign');
const {cloneDeep, head} = require('lodash');

function security(state = {user: null, errorCause: null}, action) {
    switch (action.type) {
        case USERMANAGER_UPDATE_USER:
            if (state.user && action.user && state.user.id === action.user.id) {
                return assign({}, state, {
                    user: cloneDeep(action.user)
                });
            }
            return state;
        case LOGIN_SUCCESS:
            const userAttributes = SecurityUtils.getUserAttributes(action.userDetails.User);
            const userUuid = head(userAttributes.filter(attribute => attribute.name.toLowerCase() === 'uuid'));
            return assign({}, state, {
                user: action.userDetails.User,
                token: userUuid && userUuid.value || '',
                authHeader: action.authHeader,
                loginError: null
            });
        case LOGIN_FAIL:
            return assign({}, state, {
                loginError: action.error
            });
        case RESET_ERROR:
            return assign({}, state, {
                loginError: null
            });
        case LOGOUT:
            return assign({}, state, {
                user: null,
                token: null,
                authHeader: null,
                loginError: null
            });
        case CHANGE_PASSWORD_SUCCESS:
            return assign({}, state, {
                user: assign({}, state.user, assign({}, action.user, {date: new Date().getUTCMilliseconds()})),
                authHeader: action.authHeader
            });
        default:
            return state;
    }
}

module.exports = security;
