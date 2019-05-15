/**
* Copyright 2016, GeoSolutions Sas.
* All rights reserved.
*
* This source code is licensed under the BSD-style license found in the
* LICENSE file in the root directory of this source tree.
*/

const {createSelector} = require('reselect');
const assign = require('object-assign');
const _ = require('lodash');

const groupsNamesSelector = (state) => {
    return state.security && state.security.groups || [];
};

const usersSelector = (state) => {
    return state.security && state.security.users || [];
};

const usersNamesSelector = createSelector(
  [usersSelector],
  users => users.map(user => user.userName)
);

const workspacesSelector = (state) => {
    return state.security && state.security.workspaces || [];
};

const workspacesNamesSelector = createSelector(
  [workspacesSelector],
  workspaces => workspaces.map(workspace => workspace.name)
);

const rulesSelector = (state) => {
    if (!state.security || !state.security.rules) {
        return [];
    }
    const rules = state.security.rules;
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

const layersSelector = (state) => {
    return state.security && state.security.layers && state.security.layers.records || [];
};

const layersNamesSelector = createSelector(
  [layersSelector],
  layers => _.uniq(layers.map(layer => layer.dc.identifier.replace(/^.*?:/g, '')))
);

module.exports = {
    groupsNamesSelector,
    usersNamesSelector,
    workspacesNamesSelector,
    workspacesSelector,
    layersNamesSelector,
    rulesSelector
};
