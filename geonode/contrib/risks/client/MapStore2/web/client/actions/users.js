/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const USERMANAGER_GETUSERS = 'USERMANAGER_GETUSERS';
const USERMANAGER_EDIT_USER = 'USERMANAGER_EDIT_USER';
const USERMANAGER_EDIT_USER_DATA = 'USERMANAGER_EDIT_USER_DATA';
const USERMANAGER_UPDATE_USER = 'USERMANAGER_UPDATE_USER';
const USERMANAGER_DELETE_USER = 'USERMANAGER_DELETE_USER';
const USERMANAGER_GETGROUPS = 'USERMANAGER_GETGROUPS';
const USERS_SEARCH_TEXT_CHANGED = 'USERS_SEARCH_TEXT_CHANGED';

const API = require('../api/GeoStoreDAO');
const {get, assign} = require('lodash');
function getUsersloading(text, start, limit) {
    return {
        type: USERMANAGER_GETUSERS,
        status: "loading",
        searchText: text,
        start,
        limit
    };
}
function getUsersSuccess(text, start, limit, users, totalCount) {
    return {
        type: USERMANAGER_GETUSERS,
        status: "success",
        searchText: text,
        start,
        limit,
        users,
        totalCount

    };
}
function getUsersError(text, start, limit, error) {
    return {
        type: USERMANAGER_GETUSERS,
        status: "error",
        searchText: text,
        start,
        limit,
        error
    };
}
function getUsers(searchText, options) {
    let params = options && options.params;
    let start;
    let limit;
    if (params) {
        start = params.start;
        limit = params.limit;
    }
    return (dispatch, getState) => {
        let text = searchText;
        let state = getState && getState();
        if (state) {
            let oldText = get(state, "users.searchText");
            text = searchText || oldText || "*";
            start = ( (start !== null && start !== undefined) ? start : (get(state, "users.start") || 0));
            limit = limit || get(state, "users.limit") || 12;
        }
        dispatch(getUsersloading(text, start, limit));

        return API.getUsers(text, {...options, params: {start, limit}}).then((response) => {
            let users;
            // this because _.get returns an array with an undefined element isntead of null
            if (!response || !response.ExtUserList || !response.ExtUserList.User) {
                users = [];
            } else {
                users = get(response, "ExtUserList.User");
            }

            let totalCount = get(response, "ExtUserList.UserCount");
            users = Array.isArray(users) ? users : [users];
            users = users.map((user) => {
                let groups = get(user, "groups.group");
                groups = Array.isArray(groups) ? groups : [groups];
                return assign({}, user, {
                    groups
                });
            });
            dispatch(getUsersSuccess(text, start, limit, users, totalCount));
        }).catch((error) => {
            dispatch(getUsersError(text, start, limit, error));
        });
    };
}

function getGroupsSuccess(groups) {
    return {
        type: USERMANAGER_GETGROUPS,
        status: "success",
        groups
    };
}

function getGroupsError(error) {
    return {
        type: USERMANAGER_GETGROUPS,
        status: "error",
        error
    };
}
function getGroups(user) {
    return (dispatch) => {
        dispatch({
            type: USERMANAGER_GETGROUPS,
            status: "loading"
        });
        return API.getAvailableGroups(user).then((groups) => {
            dispatch(getGroupsSuccess(groups));
        }).catch((error) => {
            dispatch(getGroupsError(error));
        });
    };

}

function editUserLoading(user) {
    return {
        type: USERMANAGER_EDIT_USER,
        status: "loading",
        user
    };
}

function editUserSuccess(userLoaded) {
    return {
        type: USERMANAGER_EDIT_USER,
        status: "success",
        user: userLoaded
    };
}

function editUserError(user, error) {
    return {
        type: USERMANAGER_EDIT_USER,
        status: "error",
        user,
        error
    };
}

function editNewUser(user) {
    return {
        type: USERMANAGER_EDIT_USER,
        user: user
    };
}
function editUser(user, options ={params: {includeattributes: true}} ) {
    return (dispatch, getState) => {
        let state = getState && getState();
        if (state) {
            // check if available groups are present
            if (!(state.users && state.users.groups)) {
                // get the current user [it should work]
                let currentUser = state.security && state.security.user;
                dispatch(getGroups(currentUser || {role: "ADMIN"}));
            }
        }
        if (user && user.id) {
            dispatch(editUserLoading(user));
            return API.getUser(user.id, options).then((userDetails) => {
                let userLoaded = userDetails.User;
                let attribute = userLoaded.attribute;
                if (attribute) {
                    userLoaded = {
                        ...userLoaded,
                        attribute: Array.isArray(attribute) ? attribute : [attribute]
                    };
                }
                // the service returns groups = "", skip this to avoid overriding
                if (userLoaded) {
                    userLoaded = {...userLoaded, groups: user.groups};
                }
                dispatch(editUserSuccess(userLoaded));
            }).catch((error) => {
                dispatch(editUserError(user, error));
            });
        }
        dispatch(editNewUser(user));
    };
}

function savingUser(user) {
    return {
        type: USERMANAGER_UPDATE_USER,
        status: "saving",
        user
    };
}

function savedUser(userDetails) {
    return {
        type: USERMANAGER_UPDATE_USER,
        status: "saved",
        user: userDetails && userDetails.User
    };
}

function saveError(user, error) {
    return {
        type: USERMANAGER_UPDATE_USER,
        status: "error",
        user,
        error
    };
}

function creatingUser(user) {
    return {
        type: USERMANAGER_UPDATE_USER,
        status: "creating",
        user
    };
}

function userCreated(id, user) {
    return {
        type: USERMANAGER_UPDATE_USER,
        status: "created",
        user: { ...user, id}
    };
}

function createError(user, error) {
    return {
        type: USERMANAGER_UPDATE_USER,
        status: "error",
        user,
        error
    };
}

function saveUser(user, options = {}) {
    return (dispatch) => {
        if (user && user.id) {
            dispatch(savingUser(user));
            return API.updateUser(user.id, {...user, groups: { group: user.groups}}, options).then((userDetails) => {
                dispatch(savedUser(userDetails));
                dispatch(getUsers());
            }).catch((error) => {
                dispatch(saveError(user, error));
            });
        }
        // createUser
        dispatch(creatingUser(user));
        let userToPost = {...user};
        if (user && user.groups) {
            userToPost = {...user, groups: { group: user.groups.filter((g) => {
                return g.groupName !== "everyone"; // see:https://github.com/geosolutions-it/geostore/issues/149
            })}};
        }
        return API.createUser(userToPost, options).then((id) => {
            dispatch(userCreated(id, user));
            dispatch(getUsers());
        }).catch((error) => {
            dispatch(createError(user, error));
        });

    };
}
function changeUserMetadata(key, newValue) {
    return {
        type: USERMANAGER_EDIT_USER_DATA,
        key,
        newValue
    };
}

function deletingUser(id) {
    return {
        type: USERMANAGER_DELETE_USER,
        status: "deleting",
        id
    };
}
function deleteUserSuccess(id) {
    return {
        type: USERMANAGER_DELETE_USER,
        status: "deleted",
        id
    };
}
function deleteUserError(id, error) {
    return {
        type: USERMANAGER_DELETE_USER,
        status: "error",
        id,
        error
    };
}

function closeDelete(status, id) {
    return {
        type: USERMANAGER_DELETE_USER,
        status,
        id
    };
}
function deleteUser(id, status = "confirm") {
    if (status === "confirm" || status === "cancelled") {
        return closeDelete(status, id);
    } else if ( status === "delete") {
        return (dispatch) => {
            dispatch(deletingUser(id));
            API.deleteUser(id).then(() => {
                dispatch(deleteUserSuccess(id));
                dispatch(getUsers());
            }).catch((error) => {
                dispatch(deleteUserError(id, error));
            });
        };
    }
}

function usersSearchTextChanged(text) {
    return {
        type: USERS_SEARCH_TEXT_CHANGED,
        text
    };
}

module.exports = {
    getUsers, USERMANAGER_GETUSERS,
    editUser, USERMANAGER_EDIT_USER,
    changeUserMetadata, USERMANAGER_EDIT_USER_DATA,
    saveUser, USERMANAGER_UPDATE_USER,
    deleteUser, USERMANAGER_DELETE_USER,
    getGroups, USERMANAGER_GETGROUPS,
    usersSearchTextChanged, USERS_SEARCH_TEXT_CHANGED
};
