/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {
    USERMANAGER_GETUSERS, USERMANAGER_EDIT_USER, USERMANAGER_EDIT_USER_DATA, USERMANAGER_UPDATE_USER, USERMANAGER_DELETE_USER,
    USERMANAGER_GETGROUPS, USERS_SEARCH_TEXT_CHANGED
} = require('../actions/users');

const {UPDATEGROUP, STATUS_CREATED, DELETEGROUP, STATUS_DELETED} = require('../actions/usergroups');
const assign = require('object-assign');

const {findIndex} = require('lodash');
/**
 * Reducer for a user
 * * It contains the following parts:
 *
 * {
 *    searchText: {string} The text string
 *    status: {string} one of "loading", "new", "saving", "error", "modified", "cancelled"
 * }
 *
 * @param {object} state - The current state
 * @param {object} action - The performed action
 *

 *
 */
function users(state = {
    start: 0,
    limit: 12
}, action) {
    switch (action.type) {
        case USERMANAGER_GETUSERS:
            return assign({}, state, {
                searchText: action.searchText,
                status: action.status,
                users: action.status === "loading" ? state.users : action.users,
                start: action.start,
                limit: action.limit,
                totalCount: action.status === "loading" ? state.totalCount : action.totalCount
            });
        case USERS_SEARCH_TEXT_CHANGED: {
            return assign({}, state, {
                searchText: action.text
            });
        }
        case USERMANAGER_EDIT_USER: {
            let newUser = action.status ? {
                status: action.status,
                ...action.user
            } : action.user;
            if (state.currentUser && action.user && (state.currentUser.id === action.user.id) ) {
                return assign({}, state, {
                    currentUser: assign({}, state.currentUser, {
                        status: action.status,
                        ...action.user
                    })}
                );
            // this to catch user loaded but window already closed
        } else if (action.status === "loading" || action.status === "new" || !action.status) {
            return assign({}, state, {
                    currentUser: newUser
                });
        }
            return state;

        }
        case USERMANAGER_EDIT_USER_DATA: {
            let k = action.key;
            let currentUser = state.currentUser;
            if ( k.indexOf("attribute") === 0) {
                let attrs = (currentUser.attribute || []).concat();
                let attrName = k.split(".")[1];
                let attrIndex = findIndex(attrs, (att) => att.name === attrName);
                if (attrIndex >= 0) {
                    attrs[attrIndex] = {name: attrName, value: action.newValue};
                } else {
                    attrs.push({name: attrName, value: action.newValue});
                }

                currentUser = assign({}, currentUser, {
                    attribute: attrs
                });
            } else {
                currentUser = assign({}, currentUser, {[k]: action.newValue} );
            }
            return assign({}, state, {
                currentUser: assign({}, {...currentUser, status: "modified"})
            });
        }
        case USERMANAGER_UPDATE_USER: {
            let currentUser = state.currentUser;

            return assign({}, state, {
               currentUser: assign({}, {
                   ...currentUser,
                   ...action.user,
                   status: action.status,
                   lastError: action.error
               })
           });
        }
        case USERMANAGER_DELETE_USER: {
            if (action.status === "deleted" || action.status === "cancelled") {
                return assign({}, state, {
                    deletingUser: null
                });
            }
            return assign({}, state, {
                deletingUser: {
                    id: action.id,
                    status: action.status,
                    error: action.error
                }
            });
        }
        case USERMANAGER_GETGROUPS: {
            return assign({}, state, {
                groups: action.groups,
                groupsStatus: action.status,
                groupsError: action.error
            });
        }
        case UPDATEGROUP: {
            if (action.status === STATUS_CREATED) {
                return assign({}, state, {
                    groups: null,
                    groupsStatus: null,
                    groupsError: null
                });
            }
            return state;
        }
        case DELETEGROUP: {
            if (action.status === STATUS_DELETED) {
                return assign({}, state, {
                    groups: null,
                    groupsStatus: null,
                    groupsError: null
                });
            }
            return state;
        }
        default:
            return state;
    }
}
module.exports = users;
