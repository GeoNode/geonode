/**
* Copyright 2016, GeoSolutions Sas.
* All rights reserved.
*
* This source code is licensed under the BSD-style license found in the
* LICENSE file in the root directory of this source tree.
*/

const expect = require('expect');
const {rulesSelector, optionsSelector} = require('../rulesmanager');

describe('test rules manager selectors', () => {

    it('test rules selector', () => {
        const state = {
            rulesmanager: {
                rules: [
                    {
                        id: "rules1",
                        priority: 1,
                        roleName: "role1",
                        access: "ALLOW"
                    }
                ]
            }
        };
        const rules = rulesSelector(state);
        expect(rules.length).toBe(1);
        expect(rules[0]).toEqual({
            id: "rules1",
            priority: 1,
            roleName: "role1",
            userName: "*",
            service: "*",
            request: "*",
            workspace: "*",
            layer: "*",
            access: "ALLOW"
        });
    });

    it('test options selector', () => {
        const state = {
            rulesmanager: {
                options: {
                    roles: ["role1"],
                    users: [
                        {userName: "user1"}
                    ],
                    workspaces: [
                        {name: "workspace1"}
                    ],
                    layers: {
                        records: [{
                            dc: {
                                identifier: "workspace:layer1"
                            }
                        }]
                    },
                    layersPage: 5,
                    layersCount: 10
                }
            }
        };
        const options = optionsSelector(state);
        expect(options).toEqual({
            roles: ["role1"],
            users: ["user1"],
            workspaces: ["workspace1"],
            layers: ["layer1"],
            layersPage: 5,
            layersCount: 10
        });
    });
});
