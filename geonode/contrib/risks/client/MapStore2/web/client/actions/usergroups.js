/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const GETGROUPS = 'GROUPMANAGER_GETGROUPS';
const EDITGROUP = 'GROUPMANAGER_EDITGROUP';
const EDITGROUPDATA = 'GROUPMANAGER_EDITGROUP_DATA';
const UPDATEGROUP = 'GROUPMANAGER_UPDATE_GROUP';
const DELETEGROUP = 'GROUPMANAGER_DELETEGROUP';
const SEARCHTEXTCHANGED = 'GROUPMANAGER_SEARCHTEXTCHANGED';
const SEARCHUSERS = 'GROUPMANAGER_SEARCHUSERS';
const STATUS_LOADING = "loading";
const STATUS_SUCCESS = "success";
const STATUS_ERROR = "error";
// const STATUS_NEW = "new";
const STATUS_SAVING = "saving";
const STATUS_SAVED = "saved";
const STATUS_CREATING = "creating";
const STATUS_CREATED = "created";
const STATUS_DELETED = "deleted";

/*
const USERGROUPMANAGER_UPDATE_GROUP = 'USERMANAGER_UPDATE_GROUP';
const USERGROUPMANAGER_DELETE_GROUP = 'USERMANAGER_DELETE_GROUP';
const USERGROUPMANAGER_SEARCH_TEXT_CHANGED = 'USERGROUPMANAGER_SEARCH_TEXT_CHANGED';
*/
const API = require('../api/GeoStoreDAO');
const {get/*, assign*/} = require('lodash');

function getUserGroupsLoading(text, start, limit) {
    return {
        type: GETGROUPS,
        status: STATUS_LOADING,
        searchText: text,
        start,
        limit
    };
}
function getUserGroupSuccess(text, start, limit, groups, totalCount) {
    return {
        type: GETGROUPS,
        status: STATUS_SUCCESS,
        searchText: text,
        start,
        limit,
        groups,
        totalCount

    };
}
function getUserGroupError(text, start, limit, error) {
    return {
        type: GETGROUPS,
        status: STATUS_ERROR,
        searchText: text,
        start,
        limit,
        error
    };
}
function getUserGroups(searchText, options) {
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
            let oldText = get(state, "usergroups.searchText");
            text = searchText || oldText || "*";
            start = ( (start !== null && start !== undefined) ? start : (get(state, "usergroups.start") || 0));
            limit = limit || get(state, "usergroups.limit") || 12;
        }
        dispatch(getUserGroupsLoading(text, start, limit));

        return API.getGroups(text, {...options, params: {start, limit}}).then((response) => {
            let groups;
            // this because _.get returns an array with an undefined element isntead of null
            if (!response || !response.ExtGroupList || !response.ExtGroupList.Group) {
                groups = [];
            } else {
                groups = get(response, "ExtGroupList.Group");
            }

            let totalCount = get(response, "ExtGroupList.GroupCount");
            groups = Array.isArray(groups) ? groups : [groups];
            dispatch(getUserGroupSuccess(text, start, limit, groups, totalCount));
        }).catch((error) => {
            dispatch(getUserGroupError(text, start, limit, error));
        });
    };
}
function editGroupLoading(group) {
    return {
        type: EDITGROUP,
        status: STATUS_LOADING,
        group
    };
}

function editGroupSuccess(group) {
    return {
        type: EDITGROUP,
        status: STATUS_SUCCESS,
        group
    };
}

function editGroupError(group, error) {
    return {
        type: EDITGROUP,
        status: STATUS_ERROR,
        group,
        error
    };
}

function editNewGroup(group) {
    return {
        type: EDITGROUP,
        group
    };
}
// NOTE: not support on server side now for editing groups
function editGroup(group, options ={params: {includeattributes: true}} ) {
    return (dispatch) => {
        if (group && group.id) {
            dispatch(editGroupLoading(group));
            return API.getGroup(group.id, options).then((groupLoaded) => {
                // the service returns restUsers = "", skip this to avoid overriding
                dispatch(editGroupSuccess(groupLoaded));
            }).catch((error) => {
                dispatch(editGroupError(group, error));
            });
        }
        dispatch(editNewGroup(group));
    };
}
function changeGroupMetadata(key, newValue) {
    return {
        type: EDITGROUPDATA,
        key,
        newValue
    };
}

function savingGroup(group) {
    return {
        type: UPDATEGROUP,
        status: STATUS_SAVING,
        group
    };
}

function savedGroup(group) {
    return {
        type: UPDATEGROUP,
        status: STATUS_SAVED,
        group: group
    };
}

function saveError(group, error) {
    return {
        type: UPDATEGROUP,
        status: STATUS_ERROR,
        group,
        error
    };
}

function creatingGroup(group) {
    return {
        type: UPDATEGROUP,
        status: STATUS_CREATING,
        group
    };
}

function groupCreated(id, group) {
    return {
        type: UPDATEGROUP,
        status: STATUS_CREATED,
        group: { ...group, id}
    };
}

function createError(group, error) {
    return {
        type: UPDATEGROUP,
        status: STATUS_ERROR,
        group,
        error
    };
}
function saveGroup(group, options = {}) {
    return (dispatch) => {
        if (group && group.id) {
            dispatch(savingGroup(group));
            return API.updateGroupMembers(group, options).then((groupDetails) => {
                dispatch(savedGroup(groupDetails));
                dispatch(getUserGroups());
            }).catch((error) => {
                dispatch(saveError(group, error));
            });
        }
        // create Group
        dispatch(creatingGroup(group));
        return API.createGroup(group, options).then((id) => {
            dispatch(groupCreated(id, group));
            dispatch(getUserGroups());
        }).catch((error) => {
            dispatch(createError(group, error));
        });

    };
}

function deletingGroup(id) {
    return {
        type: DELETEGROUP,
        status: "deleting",
        id
    };
}
function deleteGroupSuccess(id) {
    return {
        type: DELETEGROUP,
        status: STATUS_DELETED,
        id
    };
}
function deleteGroupError(id, error) {
    return {
        type: DELETEGROUP,
        status: STATUS_ERROR,
        id,
        error
    };
}

function closeDelete(status, id) {
    return {
        type: DELETEGROUP,
        status,
        id
    };
}
function deleteGroup(id, status = "confirm") {
    if (status === "confirm" || status === "cancelled") {
        return closeDelete(status, id);
    } else if ( status === "delete") {
        return (dispatch) => {
            dispatch(deletingGroup(id));
            API.deleteGroup(id).then(() => {
                dispatch(deleteGroupSuccess(id));
                dispatch(getUserGroups());
            }).catch((error) => {
                dispatch(deleteGroupError(id, error));
            });
        };
    }
}

function groupSearchTextChanged(text) {
    return {
        type: SEARCHTEXTCHANGED,
        text
    };
}
function searchUsersSuccessLoading() {
    return {
        type: SEARCHUSERS,
        status: STATUS_LOADING
    };
}
function searchUsersSuccess(users) {
    return {
        type: SEARCHUSERS,
        status: STATUS_SUCCESS,
        users
    };
}
function searchUsersError(error) {
    return {
        type: SEARCHUSERS,
        status: STATUS_ERROR,
        error
    };
}
function searchUsers(text ="*", start = 0, limit = 5, options = {}, jollyChar = "*") {
    return (dispatch) => {
        dispatch(searchUsersSuccessLoading(text, start, limit));
        return API.getUsers(jollyChar + text + jollyChar, {...options, params: {start, limit}}).then((response) => {
            let users;
            // this because _.get returns an array with an undefined element instead of null
            if (!response || !response.ExtUserList || !response.ExtUserList.User) {
                users = [];
            } else {
                users = get(response, "ExtUserList.User");
            }
            users = Array.isArray(users) ? users : [users];
            dispatch(searchUsersSuccess(users));
        }).catch((error) => {
            dispatch(searchUsersError(error));
        });
    };
}

module.exports = {
    getUserGroups, GETGROUPS,
    editGroup, EDITGROUP,
    changeGroupMetadata, EDITGROUPDATA,
    groupSearchTextChanged, SEARCHTEXTCHANGED,
    searchUsers, SEARCHUSERS,
    saveGroup, UPDATEGROUP,
    deleteGroup, DELETEGROUP,
    STATUS_SUCCESS,
    STATUS_LOADING,
    STATUS_CREATED,
    STATUS_ERROR,
    STATUS_DELETED
};
