/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const axios = require('../../libs/ajax');
const assign = require('object-assign');

const ConfigUtils = require('../../utils/ConfigUtils');

var Api = {

    loadRules: function(rulesPage, rulesFiltersValues) {
        const options = {
            'params': {
                'page': rulesPage - 1,
                'entries': 10
            }
        };
        this.assignFiltersValue(rulesFiltersValues, options);
        return axios.get('geofence/rest/rules', this.addBaseUrl(options))
            .then(function(response) {
                return response.data;
            }
        );
    },

    getRulesCount: function(rulesFiltersValues) {
        const options = {
            'params': {}
        };
        this.assignFiltersValue(rulesFiltersValues, options);
        return axios.get('geofence/rest/rules/count', this.addBaseUrl(options)).then(function(response) {
            return response.data;
        });
    },

    moveRules: function(targetPriority, rules) {
        const options = {
            'params': {
                'targetPriority': targetPriority,
                'rulesIds': rules && rules.map(rule => rule.id).join()
            }
        };
        return axios.get('geofence/rest/rules/move', this.addBaseUrl(options)).then(function(response) {
            return response.data;
        });
    },

    deleteRule: function(ruleId) {
        return axios.delete('geofence/rest/rules/id/' + ruleId, this.addBaseUrl({}));
    },

    addRule: function(rule) {
        if (!rule.access) {
            rule.access = "ALLOW";
        }
        return axios.post('geofence/rest/rules', rule, this.addBaseUrl({
            'headers': {
                'Content': 'application/json'
            }
        }));
    },

    updateRule: function(rule) {
        return axios.post('geofence/rest/rules/id/' + rule.id, rule, this.addBaseUrl({
            'headers': {
                'Content': 'application/json'
            }
        }));
    },

    assignFiltersValue: function(rulesFiltersValues, options) {
        if (rulesFiltersValues) {
            assign(options.params, {"userName": this.normalizeFilterValue(rulesFiltersValues.userName)});
            assign(options.params, {"roleName": this.normalizeFilterValue(rulesFiltersValues.roleName)});
            assign(options.params, {"service": this.normalizeFilterValue(rulesFiltersValues.service)});
            assign(options.params, {"request": this.normalizeFilterValue(rulesFiltersValues.request)});
            assign(options.params, {"workspace": this.normalizeFilterValue(rulesFiltersValues.workspace)});
            assign(options.params, {"layer": this.normalizeFilterValue(rulesFiltersValues.layer)});
        }
        return options;
    },

    normalizeFilterValue(value) {
        return value === "*" ? undefined : value;
    },

    assignFilterValue: function(queryParameters, filterName, filterAny, filterValue) {
        if (!filterValue) {
            return;
        }
        if (filterValue === '*') {
            assign(queryParameters, {[filterAny]: 1});
        } else {
            assign(queryParameters, {[filterName]: filterValue});
        }
    },

    getGroups: function() {
        return axios.get('security/rest/roles', this.addBaseUrl({
            'headers': {
                'Accept': 'application/json'
            }
        })).then(function(response) {
            return response.data;
        });
    },

    getUsers: function() {
        return axios.get('security/rest/usergroup/users', this.addBaseUrl({
            'headers': {
                'Accept': 'application/json'
            }
        })).then(function(response) {
            return response.data;
        });
    },

    getWorkspaces: function() {
        return axios.get('rest/workspaces', this.addBaseUrl({
            'headers': {
                'Accept': 'application/json'
            }
        })).then(function(response) {
            return response.data;
        });
    },

    nullToAny: function(value) {
        return !value ? '*' : value;
    },

    addBaseUrl: function(options) {
        return assign(options, {baseURL: ConfigUtils.getDefaults().geoServerUrl});
    }
};

module.exports = Api;
