/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const GeoServerAPI = require('../api/geoserver/GeoFence');

const axios = require('../libs/ajax');
const CatalogAPI = require('../api/CSW');
const ConfigUtils = require('../utils/ConfigUtils');

const RULES_SELECTED = 'RULES_SELECTED';
const RULES_LOADED = 'RULES_LOADED';
const UPDATE_ACTIVE_RULE = 'UPDATE_ACTIVE_RULE';
const UPDATE_FILTERS_VALUES = 'UPDATE_FILTERS_VALUES';
const ACTION_ERROR = 'ACTION_ERROR';
const OPTIONS_LOADED = 'OPTIONS_LOADED';

function rulesSelected(rules, merge, unselect) {
    return {
        type: RULES_SELECTED,
        rules: rules,
        merge: merge,
        unselect: unselect
    };
}

function rulesLoaded(rules, count, page, keepSelected) {
    return {
        type: RULES_LOADED,
        rules: rules.rules,
        count: count.count,
        page: page,
        keepSelected: keepSelected
    };
}

function updateActiveRule(rule, status, merge) {
    return {
        type: UPDATE_ACTIVE_RULE,
        rule: rule,
        status: status,
        merge: merge
    };
}

function actionError(msgId, context) {
    return {
        type: ACTION_ERROR,
        msgId: msgId,
        context: context
    };
}

function optionsLoaded(name, values, page, valuesCount) {
    return {
        type: OPTIONS_LOADED,
        name: name,
        values: values,
        page: page,
        valuesCount: valuesCount
    };
}

function updateFiltersValues(filtersValues) {
    return {
        type: UPDATE_FILTERS_VALUES,
        filtersValues: filtersValues
    };
}

function loadRoles(context) {
    return (dispatch) => {
        GeoServerAPI.getGroups().then((result) => {
            dispatch(optionsLoaded('roles', result.roles));
        }).catch(() => {
            dispatch(actionError("rulesmanager.errorLoadingRoles", context));
        });
    };
}

function loadUsers(context) {
    return (dispatch) => {
        GeoServerAPI.getUsers().then((result) => {
            dispatch(optionsLoaded('users', result.users));
        }).catch(() => {
            dispatch(actionError("rulesmanager.errorLoadingUsers", context));
        });
    };
}

function loadWorkspaces(context) {
    return (dispatch) => {
        GeoServerAPI.getWorkspaces().then((result) => {
            dispatch(optionsLoaded('workspaces', result.workspaces.workspace));
        }).catch(() => {
            dispatch(actionError("rulesmanager.errorLoadingWorkspaces", context));
        });
    };
}

function loadLayers(input, workspace, page, context) {
    return (dispatch) => {
        const catalogUrl = ConfigUtils.getDefaults().geoServerUrl + 'csw';
        CatalogAPI.workspaceSearch(catalogUrl, (page - 1) * 10 + 1, 10, input, workspace, page).then((layers) => {
            dispatch(optionsLoaded('layers', layers, page, layers.numberOfRecordsMatched));
        }).catch(() => {
            dispatch(actionError("rulesmanager.errorLoadingLayers", context));
        });
    };
}

function loadRules(page, keepSelected) {
    return (dispatch, getState) => {
        const state = getState().rulesmanager || {};
        const filtersValues = state.filtersValues || {};
        axios.all([GeoServerAPI.loadRules(page, filtersValues),
                   GeoServerAPI.getRulesCount(filtersValues)])
            .then(axios.spread((rules, count) => {
                dispatch(rulesLoaded(rules, count, page, keepSelected));
            })).catch(() => {
                dispatch(actionError("rulesmanager.errorLoadingRules", "table"));
            }
        );
    };
}

function moveRules(targetPriority, rules) {
    return (dispatch, getSate) => {
        GeoServerAPI.moveRules(targetPriority, rules).then(() => {
            const state = getSate().rulesmanager || {};
            dispatch(loadRules(state.rulesPage || 1, true));
        }).catch(() => {
            dispatch(actionError("rulesmanager.errorMovingRules", "table"));
        });
    };
}

function moveRulesToPage(targetPage, forward, rules) {
    return (dispatch, getState) => {
        const state = getState().rulesmanager || {};
        const filtersValues = state.filtersValues || {};
        GeoServerAPI.loadRules(targetPage, filtersValues)
        .then((targetPageRules) => {
            let index = 0;
            if (forward) {
                index = Math.min(rules.length - 1, targetPageRules.rules.length - 1);
            }
            let targetPriority = targetPageRules.rules[index].priority;
            if (forward) {
                targetPriority = targetPriority + 1;
            }
            GeoServerAPI.moveRules(targetPriority, rules).then(() => {
                dispatch(loadRules(targetPage, true));
            }).catch(() => {
                dispatch(actionError("rulesmanager.errorMovingRules", "table"));
            });
        }).catch(() => {
            dispatch(actionError("rulesmanager.errorLoadingRules", "table"));
        });
    };
}

function deleteRules() {
    return (dispatch, getState) => {
        const state = getState().rulesmanager || {};
        const rules = state.selectedRules || [];
        const calls = rules.map(rule => GeoServerAPI.deleteRule(rule.id));
        axios.all(calls).then(() => {
            dispatch(loadRules(state.rulesPage || 1));
        }).catch(() => {
            dispatch(actionError("rulesmanager.errorDeletingRules", "table"));
        });
    };
}

function addRule() {
    return (dispatch, getState) => {
        const state = getState().rulesmanager || {};
        const activeRule = state && state.activeRule || {};
        const rulesPage = state.rulesPage || 1;
        GeoServerAPI.addRule(activeRule.rule).then(() => {
            dispatch(loadRules(rulesPage, true));
        }).catch(() => {
            dispatch(actionError("rulesmanager.errorAddingRule", "modal"));
        });
    };
}

function updateRule() {
    return (dispatch, getState) => {
        const state = getState().rulesmanager || {};
        const activeRule = state && state.activeRule || {};
        const rulesPage = state.rulesPage || 1;
        GeoServerAPI.updateRule(activeRule.rule).then(() => {
            dispatch(loadRules(rulesPage, true));
        }).catch(() => {
            dispatch(actionError("rulesmanager.errorUpdatingRule", "modal"));
        });
    };
}

module.exports = {
    RULES_SELECTED,
    RULES_LOADED,
    UPDATE_ACTIVE_RULE,
    UPDATE_FILTERS_VALUES,
    ACTION_ERROR,
    OPTIONS_LOADED,
    rulesLoaded,
    rulesSelected,
    loadRules,
    moveRules,
    moveRulesToPage,
    updateActiveRule,
    updateFiltersValues,
    deleteRules,
    addRule,
    updateRule,
    loadRoles,
    loadUsers,
    loadWorkspaces,
    loadLayers,
    actionError,
    optionsLoaded
};
