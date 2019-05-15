/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var rulesmanager = require('../rulesmanager');

describe('test rules manager reducer', () => {

    it('returns original state on unrecognized action', () => {
        var state = rulesmanager(1, {type: 'UNKNOWN'});
        expect(state).toBe(1);
    });

    it('substitute selected rules', () => {
        const oldState = {
            selectedRules: [
                { id: "rules1" },
                { id: "rules2" }
            ]
        };
        var state = rulesmanager(oldState, {
            type: 'RULES_SELECTED',
            merge: false,
            unselect: false,
            rules: [
                { id: "rules3" },
                { id: "rules4" }
            ]
        });
        expect(state.selectedRules.length).toBe(2);
        expect(state.selectedRules).toInclude({ id: "rules3" });
        expect(state.selectedRules).toInclude({ id: "rules4" });
    });

    it('merge selected rules', () => {
        const oldState = {
            selectedRules: [
                { id: "rules1" },
                { id: "rules2" }
            ]
        };
        var state = rulesmanager(oldState, {
            type: 'RULES_SELECTED',
            merge: true,
            unselect: false,
            rules: [
                { id: "rules3" },
                { id: "rules4" }
            ]
        });
        expect(state.selectedRules.length).toBe(4);
        expect(state.selectedRules).toInclude({ id: "rules1" });
        expect(state.selectedRules).toInclude({ id: "rules2" });
        expect(state.selectedRules).toInclude({ id: "rules3" });
        expect(state.selectedRules).toInclude({ id: "rules4" });
    });

    it('substitute unselected rules', () => {
        const oldState = {
            selectedRules: [
                { id: "rules1" },
                { id: "rules2" },
                { id: "rules3" },
                { id: "rules4" }
            ]
        };
        var state = rulesmanager(oldState, {
            type: 'RULES_SELECTED',
            merge: false,
            unselect: true,
            rules: [
                { id: "rules3" },
                { id: "rules4" }
            ]
        });
        expect(state.selectedRules.length).toBe(2);
        expect(state.selectedRules).toInclude({ id: "rules3" });
        expect(state.selectedRules).toInclude({ id: "rules4" });
    });

    it('merge unselected rules', () => {
        const oldState = {
            selectedRules: [
                { id: "rules1" },
                { id: "rules2" },
                { id: "rules3" },
                { id: "rules4" }
            ]
        };
        var state = rulesmanager(oldState, {
            type: 'RULES_SELECTED',
            merge: true,
            unselect: true,
            rules: [
                { id: "rules3" },
                { id: "rules4" }
            ]
        });
        expect(state.selectedRules.length).toBe(2);
        expect(state.selectedRules).toInclude({ id: "rules1" });
        expect(state.selectedRules).toInclude({ id: "rules2" });
    });

    it('load rules not keeping selected rules', () => {
        const oldState = {
            rules: [
                { id: "rules1" },
                { id: "rules2" }
            ],
            rulesCount: 15,
            rulesPage: 1,
            selectedRules: [
                { id: "rules3" },
                { id: "rules4" }
            ],
            activeRule: { id: "rules5" },
            error: { msgId: "error" }
        };
        var state = rulesmanager(oldState, {
            type: 'RULES_LOADED',
            rules: [
                { id: "rules6" },
                { id: "rules7" }
            ],
            count: 20,
            page: 2,
            keepSelected: false
        });
        expect(state.rules.length).toBe(2);
        expect(state.rules).toInclude({ id: "rules6" });
        expect(state.rules).toInclude({ id: "rules7" });
        expect(state.rulesCount).toBe(20);
        expect(state.rulesPage).toBe(2);
        expect(state.selectedRules.length).toBe(0);
        expect(state.activeRule).toEqual({});
        expect(state.error).toEqual({});
    });

    it('load rules keeping selected rules', () => {
        const oldState = {
            rules: [
                { id: "rules1" },
                { id: "rules2" }
            ],
            rulesCount: 15,
            rulesPage: 1,
            selectedRules: [
                { id: "rules3" },
                { id: "rules4" }
            ],
            activeRule: { id: "rules5" },
            error: { msgId: "error" }
        };
        var state = rulesmanager(oldState, {
            type: 'RULES_LOADED',
            rules: [
                { id: "rules6" },
                { id: "rules7" }
            ],
            count: 20,
            page: 2,
            keepSelected: true
        });
        expect(state.rules.length).toBe(2);
        expect(state.rules).toInclude({ id: "rules6" });
        expect(state.rules).toInclude({ id: "rules7" });
        expect(state.rulesCount).toBe(20);
        expect(state.rulesPage).toBe(2);
        expect(state.selectedRules.length).toBe(2);
        expect(state.selectedRules).toInclude({ id: "rules3" });
        expect(state.selectedRules).toInclude({ id: "rules4" });
        expect(state.activeRule).toEqual({});
        expect(state.error).toEqual({});
    });

    it('update active rule by substituing values', () => {
        const oldState = {
            activeRule: {
                rule: {
                    id: "rules1",
                    value1: "value1"
                },
                status: "status1"
            }
        };
        var state = rulesmanager(oldState, {
            type: 'UPDATE_ACTIVE_RULE',
            rule: {
                id: "rules2",
                value2: "value2"
            },
            status: "status2",
            merge: false
        });
        expect(state.activeRule.rule).toEqual({
            id: "rules2",
            value2: "value2"
        });
        expect(state.activeRule.status).toBe("status2");
    });

    it('update active rule by merging values', () => {
        const oldState = {
            activeRule: {
                rule: {
                    id: "rules1",
                    value1: "value1"
                },
                status: "status1"
            }
        };
        var state = rulesmanager(oldState, {
            type: 'UPDATE_ACTIVE_RULE',
            rule: {
                id: "rules2",
                value2: "value2"
            },
            status: "status2",
            merge: true
        });
        expect(state.activeRule.rule).toEqual({
            id: "rules2",
            value1: "value1",
            value2: "value2"
        });
        expect(state.activeRule.status).toBe("status2");
    });

    it('update filters values', () => {
        const oldState = {
            filtersValues: {
                filter1: "value1",
                filter2: "value2"
            }
        };
        var state = rulesmanager(oldState, {
            type: 'UPDATE_FILTERS_VALUES',
            filtersValues: {
                filter1: "value4",
                filter3: "value3"
            }
        });
        expect(state.filtersValues).toEqual({
            filter1: "value4",
            filter2: "value2",
            filter3: "value3"
        });
    });

    it('action error submission', () => {
        const oldState = {
            error: {
                msgId: "msg1",
                context: "context1"
            }
        };
        var state = rulesmanager(oldState, {
            type: 'ACTION_ERROR',
            msgId: "msg2",
            context: "context2"
        });
        expect(state.error).toEqual({
            msgId: "msg2",
            context: "context2"
        });
    });

    it('options loaded', () => {
        const oldState = {
            options: {
                groups: [
                    "group1",
                    "group2"
                ],
                layers: [
                    "layer1",
                    "layer2"
                ]
            }
        };
        var state = rulesmanager(oldState, {
            type: 'OPTIONS_LOADED',
            name: "layers",
            values: [
                "layer3",
                "layer4"
            ],
            page: 10,
            valuesCount: 20
        });
        expect(state.options.groups.length).toBe(2);
        expect(state.options.groups).toInclude("group1");
        expect(state.options.groups).toInclude("group2");
        expect(state.options.layers.length).toBe(2);
        expect(state.options.layers).toInclude("layer3");
        expect(state.options.layers).toInclude("layer4");
        expect(state.options.layersPage).toBe(10);
        expect(state.options.layersCount).toBe(20);
    });
});
