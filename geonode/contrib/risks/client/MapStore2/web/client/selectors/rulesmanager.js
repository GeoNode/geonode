/**
* Copyright 2016, GeoSolutions Sas.
* All rights reserved.
*
* This source code is licensed under the BSD-style license found in the
* LICENSE file in the root directory of this source tree.
*/

const assign = require('object-assign');
const _ = require('lodash');

const rulesSelector = (state) => {
    if (!state.rulesmanager || !state.rulesmanager.rules) {
        return [];
    }
    const rules = state.rulesmanager.rules;
    return rules.map(rule => {
        const formattedRule = {};
        assign(formattedRule, {'id': rule.id});
        assign(formattedRule, {'priority': rule.priority});
        assign(formattedRule, {'roleName': rule.roleName ? rule.roleName : '*'});
        assign(formattedRule, {'userName': rule.userName ? rule.userName : '*'});
        assign(formattedRule, {'service': rule.service ? rule.service : '*'});
        assign(formattedRule, {'request': rule.request ? rule.request : '*'});
        assign(formattedRule, {'workspace': rule.workspace ? rule.workspace : '*'});
        assign(formattedRule, {'layer': rule.layer ? rule.layer : '*'});
        assign(formattedRule, {'access': rule.access});
        return formattedRule;
    });
};

const optionsSelector = (state) => {
    const stateOptions = state.rulesmanager && state.rulesmanager.options || {};
    const options = {};
    options.roles = stateOptions.roles;
    options.users = stateOptions.users && stateOptions.users.map(user => user.userName);
    options.workspaces = stateOptions.workspaces
        && stateOptions.workspaces.map(workspace => workspace.name);
    options.layers = stateOptions.layers && stateOptions.layers.records
        && _.uniq(stateOptions.layers.records.map(layer => layer.dc.identifier.replace(/^.*?:/g, '')));
    options.layersPage = stateOptions.layersPage || 1;
    options.layersCount = stateOptions.layersCount || 0;
    return options;
};

module.exports = {
    rulesSelector,
    optionsSelector
};
