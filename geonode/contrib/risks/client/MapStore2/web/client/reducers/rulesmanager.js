/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const assign = require('object-assign');

const { RULES_SELECTED, RULES_LOADED, UPDATE_ACTIVE_RULE,
        ACTION_ERROR, OPTIONS_LOADED, UPDATE_FILTERS_VALUES } = require('../actions/rulesmanager');
const _ = require('lodash');

function rulesmanager(state = {}, action) {
    switch (action.type) {
        case RULES_SELECTED: {
            if (!action.merge) {
                return assign({}, state, {
                    selectedRules: action.rules
                });
            }
            const newRules = action.rules || [];
            const existingRules = state.selectedRules || [];
            if (action.unselect) {
                return assign({}, state, {
                    selectedRules: _(existingRules).filter(
                        rule => !_.head(newRules.filter(unselected => unselected.id === rule.id))).value()
                });
            }
            return assign({}, state, {
                selectedRules: _(existingRules).concat(newRules).uniq(rule => rule.id).value()
            });
        }
        case RULES_LOADED: {
            return assign({}, state, {
                rules: action.rules,
                rulesCount: action.count,
                rulesPage: action.page,
                selectedRules: action.keepSelected ? state.selectedRules : [],
                activeRule: {},
                error: {}
            });
        }
        case UPDATE_ACTIVE_RULE: {
            if (!action.merge) {
                return assign({}, state, {
                    error: {},
                    activeRule: {
                        rule: action.rule,
                        status: action.status
                    }
                });
            }
            const rule = state.activeRule || {};
            return assign({}, state, {
                error: {},
                activeRule: {
                    rule: assign({}, rule.rule, action.rule),
                    status: action.status
                }
            });
        }
        case UPDATE_FILTERS_VALUES: {
            const filtersValues = state.filtersValues || {};
            return assign({}, state, {
                filtersValues: assign({}, filtersValues, action.filtersValues)
            });
        }
        case ACTION_ERROR: {
            return assign({}, state, {
                error: {
                    msgId: action.msgId,
                    context: action.context
                }
            });
        }
        case OPTIONS_LOADED: {
            return assign({}, state, {
                options: assign({}, state.options, {
                    [action.name]: action.values || [],
                    [action.name + "Page"]: action.page,
                    [action.name + "Count"]: action.valuesCount
                })
            });
        }
        default:
            return state;
    }
}

module.exports = rulesmanager;
