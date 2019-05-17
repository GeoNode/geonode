/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');
var security = require('../security');
var {LOGIN_SUCCESS, LOGIN_FAIL, RESET_ERROR, LOGOUT} = require('../../actions/security');
var {USERMANAGER_UPDATE_USER} = require('../../actions/users');

describe('Test the security reducer', () => {
    let testToken = "260a670e-4dc0-4719-8bc9-85555d7dcbe1";
    let testUser = {
        "User": {
            "attribute": [
               {
                  "name": "company",
                  "value": "Some Company"
               },
               {
                  "name": "email",
                  "value": "user@email.com"
               },
               {
                  "name": "notes",
                  "value": "some notes"
               },
               {
                  "name": "UUID",
                  "value": testToken
               }
            ],
            "enabled": true,
            "groups": {
               "group": {
                  "enabled": true,
                  "groupName": "everyone",
                  "id": 3
               }
            },
            "id": 6,
            "name": "user",
            "role": "USER"
        }
    };
    let testAuthHeader = "Basic dGVzdDp0ZXN0"; // test:test
    let testError = {state: 0};
    it('login state', () => {
        let state = security({}, {type: LOGIN_SUCCESS, userDetails: testUser, authHeader: testAuthHeader});
        expect(state).toExist();
        expect(state.user.name).toBe("user");
        expect(state.authHeader).toBe(testAuthHeader);
        expect(state.token).toBe(testToken);
    });
    it('login fail', () => {
        let state = security({}, {type: LOGIN_FAIL, error: testError});
        expect(state).toExist();
        expect(state.loginError).toExist(testError);
        expect(state.loginError.state).toBe(0);

    });
    it('reset error', () => {
        let state = security({}, {type: RESET_ERROR});
        expect(state).toExist();
    });
    it('logout', () => {
        let state = security({}, {type: LOGOUT});
        expect(state).toExist();
        expect(!state.user).toBe(true);
    });
    it('update user', () => {
        let state = security({user: testUser.User}, {type: USERMANAGER_UPDATE_USER, user: {
            id: 6,
            name: "changed"
        }});
        expect(state).toExist();
        expect(state.user.name).toBe("changed");
    });

    it('do not update user', () => {
        let state = security({user: testUser.User}, {type: USERMANAGER_UPDATE_USER, user: {
            id: 7,
            name: "changed"
        }});
        expect(state).toExist();
        expect(state.user.name).toBe("user");
    });
});
