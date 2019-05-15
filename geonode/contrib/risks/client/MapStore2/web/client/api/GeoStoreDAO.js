/**
 * Copyright 2015-2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const axios = require('../libs/ajax');
const _ = require('lodash');
const assign = require('object-assign');

const ConfigUtils = require('../utils/ConfigUtils');
const {findIndex} = require('lodash');

let parseOptions = (opts) => opts;

let parseAdminGroups = (groupsObj) => {
    if (!groupsObj || !groupsObj.UserGroupList || !groupsObj.UserGroupList.UserGroup || !_.isArray(groupsObj.UserGroupList.UserGroup)) return [];
    return groupsObj.UserGroupList.UserGroup.filter(obj => !!obj.id).map((obj) => _.pick(obj, ["id", "groupName", "description"]));
};

let parseUserGroups = (groupsObj) => {
    if (!groupsObj || !groupsObj.User || !groupsObj.User.groups || !groupsObj.User.groups.group || !_.isArray(groupsObj.User.groups.group)) return [];
    return groupsObj.User.groups.group.filter(obj => !!obj.id).map((obj) => _.pick(obj, ["id", "groupName", "description"]));
};


/**
 * API for local config
 */
var Api = {
    getData: function(id, options) {
        let url = "data/" + id;
        return axios.get(url, this.addBaseUrl(parseOptions(options))).then(function(response) {
            return response.data;
        });
    },
    getResource: function(resourceId, options) {
        return axios.get(
            "resources/resource/" + resourceId,
            this.addBaseUrl(parseOptions(options))).then(function(response) {return response.data; });
    },
    getResourcesByCategory: function(category, query, options) {
        let q = query || "*";
        let url = "extjs/search/category/" + category + "/*" + q + "*/thumbnail"; // comma-separated list of wanted attributes
        return axios.get(url, this.addBaseUrl(parseOptions(options))).then(function(response) {return response.data; });
    },
    basicLogin: function(username, password, options) {
        let url = "users/user/details";
        return axios.get(url, this.addBaseUrl(_.merge({
            auth: {
                username: username,
                password: password
            },
            params: {
                includeattributes: true
            }
        }, options))).then(function(response) {
            return response.data;
        });
    },
    changePassword: function(user, newPassword, options) {
        return axios.put(
            "users/user/" + user.id, "<User><newPassword>" + newPassword + "</newPassword></User>",
            this.addBaseUrl(_.merge({
                headers: {
                    'Content-Type': "application/xml"
                }
            }, options)));
    },
    addBaseUrl: function(options) {
        return assign(options, {baseURL: ConfigUtils.getDefaults().geoStoreUrl});
    },
    updateResourceAttribute: function(resourceId, name, value, type, options) {
        return axios.put(
            "resources/resource/" + resourceId + "/attributes/" + name + "/" + value, null,
            this.addBaseUrl(_.merge({
                headers: {
                    'Content-Type': "application/xml"
                }
            }, options)));
    },
    putResourceMetadata: function(resourceId, newName, newDescription, options) {
        return axios.put(
            "resources/resource/" + resourceId,
            "<Resource><description>" + (newDescription || "") + "</description><metadata></metadata>" +
            "<name>" + (newName || "") + "</name></Resource>",
            this.addBaseUrl(_.merge({
                headers: {
                    'Content-Type': "application/xml"
                }
            }, options)));
    },
    putResource: function(resourceId, content, options) {
        return axios.put(
            "data/" + resourceId,
            content,
            this.addBaseUrl(_.merge({
                headers: {
                    'Content-Type': "application/json"
                }
            }, options)));
    },
    updateResourcePermissions: function(resourceId, securityRules) {
        let payload = "<SecurityRuleList>";
        for (let rule of securityRules.SecurityRuleList.SecurityRule) {
            if (rule.canRead || rule.canWrite) {
                if (rule.user) {
                    payload = payload + "<SecurityRule>";
                    payload = payload + "<canRead>" + ((rule.canRead || rule.canWrite) ? "true" : "false") + "</canRead>";
                    payload = payload + "<canWrite>" + (rule.canWrite ? "true" : "false") + "</canWrite>";
                    payload = payload + "<user><id>" + (rule.user.id || "") + "</id><name>" + (rule.user.name || "") + "</name></user>";
                    payload = payload + "</SecurityRule>";
                } else if (rule.group) {
                    payload = payload + "<SecurityRule>";
                    payload = payload + "<canRead>" + ((rule.canRead || rule.canWrite) ? "true" : "false") + "</canRead>";
                    payload = payload + "<canWrite>" + (rule.canWrite ? "true" : "false") + "</canWrite>";
                    payload = payload + "<group><id>" + (rule.group.id || "") + "</id><groupName>" + (rule.group.groupName || "") + "</groupName></group>";
                    payload = payload + "</SecurityRule>";
                }
                // NOTE: if rule has no group or user, it is skipped
                // NOTE: if rule is "no read and no write", it is skipped
            }
        }
        payload = payload + "</SecurityRuleList>";
        return axios.post(
            "resources/resource/" + resourceId + "/permissions",
            payload,
            this.addBaseUrl({
                headers: {
                    'Content-Type': "application/xml"
                }
            }));
    },
    createResource: function(metadata, data, category, options) {
        let name = metadata.name;
        let description = metadata.description || "";
        // filter attributes from the metadata object excluding the default ones
        let attributes = metadata.attributes || _.pick(metadata, Object.keys(metadata).filter(function(key) {
            return key !== "name" && key !== "description" && key !== "id";
        }));

        let xmlAttrs = Object.keys(attributes).map((key) => {
            return "<attribute><name>" + key + "</name><value>" + attributes[key] + "</value><type>STRING</type></attribute>";
        });
        let attributesSection = "";
        if (xmlAttrs.length > 0) {
            attributesSection = "<Attributes>" + xmlAttrs.join("") + "</Attributes>";
        }
        return axios.post(
            "resources/",
                "<Resource><description>" + description + "</description><metadata></metadata>" +
                "<name>" + (name || "") + "</name><category><name>" + (category || "") + "</name></category>" +
                attributesSection +
                "<store><data><![CDATA[" + (data || "") + "]]></data></store></Resource>",
            this.addBaseUrl(_.merge({
                headers: {
                    'Content-Type': "application/xml"
                }
            }, options)));
    },
    deleteResource: function(resourceId, options) {
        return axios.delete(
            "resources/resource/" + resourceId,
            this.addBaseUrl(_.merge({
            }, options)));
    },
    getUserGroups: function(options) {
        let url = "usergroups/";
        return axios.get(url, this.addBaseUrl(parseOptions(options))).then(function(response) {
            return response.data;
        });
    },
    getPermissions: function(mapId, options) {
        let url = "resources/resource/" + mapId + "/permissions";
        return axios.get(url, this.addBaseUrl(parseOptions(options))).then(function(response) {return response.data; });
    },
    getAvailableGroups: function(user) {
        if (user && user.role === "ADMIN") {
            return axios.get(
                "usergroups/?all=true",
                this.addBaseUrl({
                    headers: {
                        'Accept': "application/json"
                    }
                })).then(function(response) {
                    return parseAdminGroups(response.data);
                });
        }
        return axios.get(
            "users/user/details",
            this.addBaseUrl({
                headers: {
                    'Accept': "application/json"
                }
            })).then(function(response) {
                return parseUserGroups(response.data);
            });
    },
    getUsers: function(textSearch, options = {}) {
        let url = "extjs/search/users" + (textSearch ? "/" + textSearch : "");
        return axios.get(url, this.addBaseUrl(parseOptions(options))).then(function(response) {return response.data; });
    },
    getUser: function(id, options = {params: {includeattributes: true}}) {
        let url = "users/user/" + id;
        return axios.get(url, this.addBaseUrl(parseOptions(options))).then(function(response) {return response.data; });
    },
    updateUser: function(id, user, options) {
        let url = "users/user/" + id;
        let postUser = assign({}, user);
        if (postUser.newPassword === "") {
            delete postUser.newPassword;
        }
        return axios.put(url, {User: postUser}, this.addBaseUrl(parseOptions(options))).then(function(response) {return response.data; });
    },
    createUser: function(user, options) {
        let url = "users/";
        let postUser = assign({}, user);
        if (postUser.newPassword) {
            postUser.password = postUser.newPassword;
        }
        return axios.post(url, {User: postUser}, this.addBaseUrl(parseOptions(options))).then(function(response) {return response.data; });
    },
    deleteUser: function(id, options = {}) {
        let url = "users/user/" + id;
        return axios.delete(url, this.addBaseUrl(parseOptions(options))).then(function(response) {return response.data; });
    },
    getGroups: function(textSearch, options = {}) {
        let url = "extjs/search/groups" + (textSearch ? "/" + textSearch : "");
        return axios.get(url, this.addBaseUrl(parseOptions(options))).then(function(response) {return response.data; });
    },
    getGroup: function(id, options = {}) {
        let url = "usergroups/group/" + id;
        return axios.get(url, this.addBaseUrl(parseOptions(options))).then(function(response) {
            let groupLoaded = response.data.UserGroup;
            let users = groupLoaded && groupLoaded.restUsers && groupLoaded.restUsers.User;
            return {...groupLoaded, users: users && (Array.isArray(users) ? users : [users]) || []};
        });
    },
    createGroup: function(group, options) {
        let url = "usergroups/";
        let groupId;
        return axios.post(url, {UserGroup: {...group}}, this.addBaseUrl(parseOptions(options)))
            .then(function(response) {
                groupId = response.data;
                return Api.updateGroupMembers({...group, id: groupId}, options);
            }).then(() => groupId);
    },
    updateGroupMembers: function(group, options) {
        // No GeoStore API to update group name and description. only update new users
        if (group.newUsers) {
            let restUsers = group.users || (group.restUsers && group.restUsers.User) || [];
            restUsers = Array.isArray(restUsers) ? restUsers : [restUsers];
            // old users not present in the new users list
            let toRemove = restUsers.filter( (user) => findIndex(group.newUsers, u => u.id === user.id) < 0);
            // new users not present in the old users list
            let toAdd = group.newUsers.filter( (user) => findIndex(restUsers, u => u.id === user.id) < 0);

            // create callbacks
            let removeCallbacks = toRemove.map( (user) => () => this.removeUserFromGroup(user.id, group.id, options) );
            let addCallbacks = toAdd.map( (user) => () => this.addUserToGroup(user.id, group.id), options );
            let requests = [...(removeCallbacks.map( call => call.call(this))), ...(addCallbacks.map(call => call()))];
            return axios.all(requests).then(() => {
                return {
                    ...group,
                    newUsers: null,
                    restUsers: { User: group.newUsers},
                    users: group.newUsers
                };
            });
        }
        return new Promise( (resolve) => {
            resolve({
                ...group
            });
        });
    },
    deleteGroup: function(id, options={}) {
        let url = "usergroups/group/" + id;
        return axios.delete(url, this.addBaseUrl(parseOptions(options))).then(function(response) {return response.data; });
    },
    addUserToGroup(userId, groupId, options = {}) {
        let url = "/usergroups/group/" + userId + "/" + groupId + "/";
        return axios.post(url, null, this.addBaseUrl(parseOptions(options)));
    },
    removeUserFromGroup(userId, groupId, options = {}) {
        let url = "/usergroups/group/" + userId + "/" + groupId + "/";
        return axios.delete(url, this.addBaseUrl(parseOptions(options)));
    }

};

module.exports = Api;
