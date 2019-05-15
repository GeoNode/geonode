/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {
    EDIT_MAP,
    UPDATE_CURRENT_MAP,
    ERROR_CURRENT_MAP,
    UPDATE_CURRENT_MAP_PERMISSIONS,
    UPDATE_CURRENT_MAP_GROUPS,
    RESET_CURRENT_MAP,
    ADD_CURRENT_MAP_PERMISSION
} = require('../actions/currentMap');

const {
    THUMBNAIL_ERROR,
    MAP_UPDATING,
    SAVE_MAP,
    DISPLAY_METADATA_EDIT,
    RESET_UPDATING,
    MAP_ERROR,
    MAP_CREATED,
    PERMISSIONS_LIST_LOADING,
    PERMISSIONS_LIST_LOADED
} = require('../actions/maps');

const assign = require('object-assign');
const _ = require('lodash');

function currentMap(state = {}, action) {
    switch (action.type) {
        case EDIT_MAP: {
            return assign({}, state, action.map, {newThumbnail: (action.map && action.map.thumbnail) ? action.map.thumbnail : null, displayMetadataEdit: true, thumbnailError: null, errors: [] });
        }
        case UPDATE_CURRENT_MAP: {
            return assign({}, state, {newThumbnail: action.thumbnail, files: action.files});
        }
        case MAP_UPDATING: {
            return assign({}, state, {updating: true});
        }
        case UPDATE_CURRENT_MAP_PERMISSIONS: {
            // Fix to overcome GeoStore bad encoding of single object arrays
            let fixedSecurityRule = [];
            if (action.permissions && action.permissions.SecurityRuleList && action.permissions.SecurityRuleList.SecurityRule) {
                if ( _.isArray(action.permissions.SecurityRuleList.SecurityRule)) {
                    fixedSecurityRule = action.permissions.SecurityRuleList.SecurityRule;
                } else {
                    fixedSecurityRule.push(action.permissions.SecurityRuleList.SecurityRule);
                }
            }
            return assign({}, state, {permissions: {
                SecurityRuleList: {
                    SecurityRule: fixedSecurityRule
                }
            }});
        }
        case UPDATE_CURRENT_MAP_GROUPS: {
            return assign({}, state, {availableGroups: action.groups});
        }
        case ADD_CURRENT_MAP_PERMISSION: {
            let newPermissions = {
                SecurityRuleList: {
                    SecurityRule: state.permissions && state.permissions.SecurityRuleList && state.permissions.SecurityRuleList.SecurityRule ? state.permissions.SecurityRuleList.SecurityRule.slice() : []
                }
            };
            if (action.rule) {
                newPermissions.SecurityRuleList.SecurityRule.push(action.rule);
            }
            return assign({}, state, { permissions: newPermissions });
        }
        case ERROR_CURRENT_MAP: {
            return assign({}, state, {thumbnailError: null, mapError: null, errors: action.errors});
        }
        case THUMBNAIL_ERROR: {
            return assign({}, state, {thumbnailError: action.error, errors: [], updating: false});
        }
        case MAP_ERROR: {
            return assign({}, state, {mapError: action.error, errors: [], updating: false});
        }
        case SAVE_MAP: {
            return assign({}, state, {thumbnailError: null});
        }
        case DISPLAY_METADATA_EDIT: {
            return assign({}, state, {displayMetadataEdit: action.displayMetadataEditValue});
        }
        case RESET_UPDATING: {
            return assign({}, state, {updating: false});
        }
        case MAP_CREATED: {
            return assign({}, state, {mapId: action.resourceId, newMapId: action.resourceId});
        }
        case PERMISSIONS_LIST_LOADING: {
            return assign({}, state, {permissionLoading: true});
        }
        case PERMISSIONS_LIST_LOADED: {
            return assign({}, state, {permissionLoading: false});
        }
        case RESET_CURRENT_MAP: {
            return {};
        }
        default:
            return state;
    }
}

module.exports = currentMap;
