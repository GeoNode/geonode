/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const EDIT_MAP = 'EDIT_MAP';
const UPDATE_CURRENT_MAP = 'UPDATE_CURRENT_MAP';
const UPDATE_CURRENT_MAP_PERMISSIONS = 'UPDATE_CURRENT_MAP_PERMISSIONS';
const UPDATE_CURRENT_MAP_GROUPS = 'UPDATE_CURRENT_MAP_GROUPS';
const ERROR_CURRENT_MAP = 'ERROR_CURRENT_MAP';
const REMOVE_THUMBNAIL = 'REMOVE_THUMBNAIL';
const RESET_CURRENT_MAP = 'RESET_CURRENT_MAP';
const ADD_CURRENT_MAP_PERMISSION = 'ADD_CURRENT_MAP_PERMISSION';

function editMap(map) {
    return {
        type: EDIT_MAP,
        map
    };
}

// update the thumbnail and the files property of the currentMap
function updateCurrentMap(files, thumbnail) {
    return {
        type: UPDATE_CURRENT_MAP,
        thumbnail,
        files
    };
}

function updateCurrentMapPermissions(permissions) {
    return {
        type: UPDATE_CURRENT_MAP_PERMISSIONS,
        permissions
    };
}

function updateCurrentMapGroups(groups) {
    return {
        type: UPDATE_CURRENT_MAP_GROUPS,
        groups
    };
}

function errorCurrentMap(errors, resourceId) {
    return {
        type: ERROR_CURRENT_MAP,
        errors,
        resourceId
    };
}

function removeThumbnail(resourceId) {
    return {
        type: REMOVE_THUMBNAIL,
        resourceId
    };
}

function resetCurrentMap() {
    return {
        type: RESET_CURRENT_MAP
    };
}

function addCurrentMapPermission(rule) {
    return {
        type: ADD_CURRENT_MAP_PERMISSION,
        rule
    };
}

module.exports = {
    EDIT_MAP, editMap,
    UPDATE_CURRENT_MAP, updateCurrentMap,
    ERROR_CURRENT_MAP, errorCurrentMap,
    REMOVE_THUMBNAIL, removeThumbnail,
    UPDATE_CURRENT_MAP_PERMISSIONS, updateCurrentMapPermissions,
    UPDATE_CURRENT_MAP_GROUPS, updateCurrentMapGroups,
    RESET_CURRENT_MAP, resetCurrentMap,
    ADD_CURRENT_MAP_PERMISSION, addCurrentMapPermission
};
