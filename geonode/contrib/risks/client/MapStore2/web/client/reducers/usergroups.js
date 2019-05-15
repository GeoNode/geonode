/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {
    GETGROUPS,
    SEARCHUSERS,
    EDITGROUP,
    EDITGROUPDATA,
    DELETEGROUP,
    UPDATEGROUP,
    SEARCHTEXTCHANGED
} = require('../actions/usergroups');
const assign = require('object-assign');
function usergroups(state = {
    start: 0,
    limit: 12
}, action) {
    switch (action.type) {
        case GETGROUPS:
            return assign({}, state, {
                searchText: action.searchText,
                status: action.status,
                groups: action.status === "loading" ? state.groups : action.groups,
                start: action.start,
                limit: action.limit,
                totalCount: action.status === "loading" ? state.totalCount : action.totalCount
            });

        case SEARCHTEXTCHANGED: {
            return assign({}, state, {
                searchText: action.text
            });
        }
        case EDITGROUP: {
            let newGroup = action.status ? {
                status: action.status,
                ...action.group
            } : action.group;
            if (state.currentGroup && action.group && (state.currentGroup.id === action.group.id) ) {
                return assign({}, state, {
                    currentGroup: assign({}, state.currentGroup, {
                        status: action.status,
                        ...action.group
                    })}
                );
            // this to catch user loaded but window already closed
        } else if (action.status === "loading" || action.status === "new" || !action.status) {
            return assign({}, state, {
                    currentGroup: newGroup
                });
        }
            return state;

        }
        case EDITGROUPDATA: {
            let k = action.key;
            let currentGroup = state.currentGroup;
            currentGroup = assign({}, currentGroup, {[k]: action.newValue} );
            return assign({}, state, {
                currentGroup: assign({}, {...currentGroup, status: "modified"})
            });
        }
        case UPDATEGROUP: {
            let currentGroup = state.currentGroup;

            return assign({}, state, {
               currentGroup: assign({}, {
                   ...currentGroup,
                   ...action.group,
                   status: action.status,
                   lastError: action.error
               })
           });
        }

        case DELETEGROUP: {
            if (action.status === "deleted" || action.status === "cancelled") {
                return assign({}, state, {
                    deletingGroup: null
                });
            }
            return assign({}, state, {
                deletingGroup: {
                    id: action.id,
                    status: action.status,
                    error: action.error
                }
            });
        }
        case SEARCHUSERS: {
            switch (action.status) {
                case "loading": {
                    return assign({}, state, {
                        availableUsersError: null,
                        availableUsersLoading: true
                    });
                }
                case "success": {
                    return assign({}, state, {
                        availableUsersError: null,
                        availableUsersLoading: false,
                        availableUsers: action.users
                    });
                }
                case "error": {
                    return assign({}, state, {
                        availableUsersError: action.error,
                        availableUsersLoading: false
                    });
                }
                default:
                    return state;
            }
        }
        default:
            return state;
    }
}
module.exports = usergroups;
