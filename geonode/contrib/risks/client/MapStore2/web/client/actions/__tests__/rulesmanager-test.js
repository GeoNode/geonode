/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const { RULES_SELECTED, RULES_LOADED, UPDATE_ACTIVE_RULE,
        ACTION_ERROR, OPTIONS_LOADED, UPDATE_FILTERS_VALUES,
        rulesSelected, rulesLoaded, updateActiveRule,
        actionError, optionsLoaded, updateFiltersValues} = require('../rulesmanager');

describe('test rules manager actions', () => {

    it('rules slected', () => {
        const rules = [
            { id: "rules1" },
            { id: "rules2" }
        ];
        var action = rulesSelected(rules, true, false);
        expect(action).toExist();
        expect(action.type).toBe(RULES_SELECTED);
        expect(action.rules.length).toBe(2);
        expect(action.rules).toInclude({ id: "rules1" });
        expect(action.rules).toInclude({ id: "rules2" });
        expect(action.merge).toBe(true);
        expect(action.unselect).toBe(false);
    });

    it('rules loaded', () => {
        const rules = {
            rules: [
                { id: "rules1" },
                { id: "rules2" }
            ]
        };
        var action = rulesLoaded(rules, {count: 10}, 5, true);
        expect(action).toExist();
        expect(action.type).toBe(RULES_LOADED);
        expect(action.rules.length).toBe(2);
        expect(action.rules).toInclude({ id: "rules1" });
        expect(action.rules).toInclude({ id: "rules2" });
        expect(action.page).toBe(5);
        expect(action.count).toBe(10);
        expect(action.keepSelected).toBe(true);
    });

    it('update active rule', () => {
        var action = updateActiveRule({ id: "rules1" }, "status", true);
        expect(action).toExist();
        expect(action.type).toBe(UPDATE_ACTIVE_RULE);
        expect(action.rule).toEqual({ id: "rules1" });
        expect(action.status).toBe("status");
        expect(action.merge).toBe(true);
    });

    it('submit action error', () => {
        var action = actionError("message", "context");
        expect(action).toExist();
        expect(action.type).toBe(ACTION_ERROR);
        expect(action.msgId).toBe("message");
        expect(action.context).toBe("context");
    });

    it('options loaded', () => {
        const groups = {
            groups: [
                { id: "group1" },
                { id: "group2" }
            ]
        };
        var action = optionsLoaded("groups", groups, 5, 25);
        expect(action).toExist();
        expect(action.type).toBe(OPTIONS_LOADED);
        expect(action.name).toBe("groups");
        expect(action.values.groups.length).toBe(2);
        expect(action.values.groups).toInclude({ id: "group1" });
        expect(action.values.groups).toInclude({ id: "group2" });
        expect(action.page).toBe(5);
        expect(action.valuesCount).toBe(25);
    });

    it('update filters values', () => {
        const filtersValues = {
            rules: [
                { group: "group1" },
                { user: "user2" }
            ]
        };
        var action = updateFiltersValues(filtersValues);
        expect(action).toExist();
        expect(action.type).toBe(UPDATE_FILTERS_VALUES);
        expect(action.filtersValues).toEqual(filtersValues);
    });
});
