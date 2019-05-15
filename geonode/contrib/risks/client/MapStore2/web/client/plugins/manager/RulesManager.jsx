/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const assign = require('object-assign');
const {connect} = require('react-redux');
const {createSelector} = require('reselect');

const { rulesSelected, loadRules, moveRules, updateActiveRule,
        deleteRules, addRule, updateRule, loadRoles, loadUsers,
        loadWorkspaces, loadLayers, updateFiltersValues, moveRulesToPage } = require('../../actions/rulesmanager');
const {rulesSelector, optionsSelector} = require('../../selectors/rulesmanager');

const genericSelector = (state, name) => state.rulesmanager && state.rulesmanager[name];

const rulesManagerSelector = createSelector([
    rulesSelector,
    optionsSelector,
    state => genericSelector(state, "rulesPage"),
    state => genericSelector(state, "rulesCount"),
    state => genericSelector(state, "selectedRules"),
    state => genericSelector(state, "activeRule"),
    state => genericSelector(state, "filtersValues"),
    state => genericSelector(state, "error")
], (rules, options, rulesPage, rulesCount, selectedRules,
    activeRule, filtersValues, error) => ({
    rules: rules,
    options: options,
    rulesPage: rulesPage,
    rulesCount: rulesCount,
    selectedRules: selectedRules,
    error: error,
    activeRule: activeRule,
    filtersValues: filtersValues
}));

const RulesManagerPlugin = connect(rulesManagerSelector, {
    onSelectRules: rulesSelected,
    moveRules: moveRules,
    moveRulesToPage: moveRulesToPage,
    loadRules: loadRules,
    updateActiveRule: updateActiveRule,
    deleteRules: deleteRules,
    addRule: addRule,
    updateRule: updateRule,
    loadRoles: loadRoles,
    loadUsers: loadUsers,
    loadWorkspaces: loadWorkspaces,
    loadLayers: loadLayers,
    updateFiltersValues: updateFiltersValues
})(require('../../components/manager/rulesmanager/RulesManager'));

module.exports = {
    RulesManagerPlugin: assign(RulesManagerPlugin, {
        hide: true,
        Manager: {
            id: "rulesmanager",
            msgId: "rulesmanager.title",
            name: 'rulesmanager',
            position: 2,
            glyph: "lock",
            title: 'Rules Manager'
        }
    }),
    reducers: {rulesmanager: require('../../reducers/rulesmanager')}
};
