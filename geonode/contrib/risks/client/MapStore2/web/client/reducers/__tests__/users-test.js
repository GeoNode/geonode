/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const expect = require('expect');

const users = require('../users');
const {
    USERMANAGER_GETUSERS, USERMANAGER_EDIT_USER, USERMANAGER_EDIT_USER_DATA,
    USERMANAGER_UPDATE_USER, USERMANAGER_DELETE_USER, USERMANAGER_GETGROUPS
} = require('../../actions/users');

const {UPDATEGROUP, STATUS_CREATED, DELETEGROUP, STATUS_DELETED} = require('../../actions/usergroups');

describe('Test the users reducer', () => {
    it('default loading', () => {
        let oldState = {test: "test"};
        const state = users(oldState, {
            type: "TEST_UNKNOWN_ACTION",
            status: 'loading'
        });
        expect(state).toBe(oldState);
    });
    it('set loading', () => {
        const state = users(undefined, {
            type: USERMANAGER_GETUSERS,
            status: 'loading'
        });
        expect(state.status).toBe('loading');
    });
    it('set users', () => {
        const state = users(undefined, {
            type: USERMANAGER_GETUSERS,
            status: 'success',
            users: [],
            totalCount: 0
        });
        expect(state.users).toExist();
        expect(state.users.length).toBe(0);
    });
    it('edit user', () => {
        const state = users(undefined, {
            type: USERMANAGER_EDIT_USER,
            user: {
                name: "user",
                attribute: [{ name: "attr1", value: "value1"}]
            },
            totalCount: 0
        });
        expect(state.currentUser).toExist();
        expect(state.currentUser.name).toBe("user");
        const stateMerge = users({currentUser: {
            id: 1,
            groups: []
        }}, {
            type: USERMANAGER_EDIT_USER,
            status: "success",
            user: {
                id: 1,
                name: "user",
                attribute: [{ name: "attr1", value: "value1"}]
            },
            totalCount: 0
        });
        expect(stateMerge.currentUser).toExist();
        expect(stateMerge.currentUser.id).toBe(1);
        expect(stateMerge.currentUser.name).toBe("user");
        expect(stateMerge.currentUser.groups).toExist();

        // action for a user not related with current.
        let newState = users(stateMerge, {
            type: USERMANAGER_EDIT_USER,
            status: "success",
            user: {
                id: 2,
                name: "NOT_THE_CURRENT_USER",
                attribute: [{ name: "attr1", value: "value1"}]
            },
            totalCount: 0
        });
        expect(newState).toBe(stateMerge);

    });
    it('edit user data', () => {
        const state = users({currentUser: {
            id: 1,
            name: "userName",
            groups: []
        }}, {
            type: USERMANAGER_EDIT_USER_DATA,
            key: "name",
            newValue: "newName"
        });
        expect(state.currentUser).toExist();
        expect(state.currentUser.id).toBe(1);
        expect(state.currentUser.name).toBe("newName");
        const stateMerge = users({currentUser: {
            id: 1,
            name: "userName",
            groups: []
        }}, {
            type: USERMANAGER_EDIT_USER_DATA,
            key: "attribute.attr1",
            newValue: "value2"
        });
        expect(stateMerge.currentUser).toExist();
        expect(stateMerge.currentUser.id).toBe(1);
        expect(stateMerge.currentUser.attribute).toExist();
        expect(stateMerge.currentUser.attribute.length).toBe(1);
        expect(stateMerge.currentUser.attribute[0].value).toBe("value2");

        // edit existing attribute
        let stateMerge2 = users(stateMerge, {
            type: USERMANAGER_EDIT_USER_DATA,
            key: "attribute.attr1",
            newValue: "NEW_VALUE"
        });
        expect(stateMerge2.currentUser).toExist();
        expect(stateMerge2.currentUser.id).toBe(1);
        expect(stateMerge2.currentUser.attribute).toExist();
        expect(stateMerge2.currentUser.attribute.length).toBe(1);
        expect(stateMerge2.currentUser.attribute[0].value).toBe("NEW_VALUE");
    });
    it('update user data', () => {
        const state = users({currentUser: {
            id: 1,
            name: "userName",
            groups: [{id: 10, groupName: "group"}]
        }}, {
            id: 1,
            name: "userName",
            groups: [{id: 10, groupName: "group"}],
            type: USERMANAGER_UPDATE_USER,
            status: "saved"
        });
        expect(state.currentUser).toExist();
        expect(state.currentUser.id).toBe(1);
    });

    it('delete user', () => {
        const state = users({users: [{
            id: 1,
            name: "userName",
            groups: []
        }]}, {
            type: USERMANAGER_DELETE_USER,
            id: 1,
            status: "delete"
        });
        expect(state.deletingUser).toExist();
        const cancelledState = users(state, {
            type: USERMANAGER_DELETE_USER,
            id: 1,
            status: "cancelled"
        });
        expect(cancelledState.deletingUser).toBe(null);
    });

    it('getGroups', () => {
        const state = users({}, {
            type: USERMANAGER_GETGROUPS,
            groups: [{groupName: "group1", id: 10, description: "test"}],
            status: "success"
        });
        expect(state.groups).toExist();
        expect(state.groupsStatus).toBe("success");
    });
    it('test group cache clean after group creation', () => {
        const state = users({}, {
            type: USERMANAGER_GETGROUPS,
            groups: [{groupName: "group1", id: 10, description: "test"}],
            status: "success"
        });
        expect(state.groups).toExist();
        expect(state.groupsStatus).toBe("success");
        let stateWOutgroups = users(state, {
            type: UPDATEGROUP,
            status: STATUS_CREATED
        });
        expect(stateWOutgroups.group).toBe(undefined);
    });
    it('test group cache clean after group delete', () => {
        const state = users({}, {
            type: USERMANAGER_GETGROUPS,
            groups: [{groupName: "group1", id: 10, description: "test"}],
            status: "success"
        });
        expect(state.groups).toExist();
        expect(state.groupsStatus).toBe("success");
        let stateWOutgroups = users(state, {
            type: DELETEGROUP,
            status: STATUS_DELETED
        });
        expect(stateWOutgroups.group).toBe(undefined);
    });

});
