/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const expect = require('expect');

const usergroups = require('../usergroups');
const {
    GETGROUPS, EDITGROUP, EDITGROUPDATA,
    SEARCHTEXTCHANGED, SEARCHUSERS, UPDATEGROUP, DELETEGROUP, STATUS_SUCCESS, STATUS_LOADING, STATUS_SAVED, STATUS_ERROR
} = require('../../actions/usergroups');

describe('Test the usergroups reducer', () => {
    it('default loading', () => {
        let oldState = {test: "test"};
        const state = usergroups(oldState, {
            type: "TEST_UNKNOWN_ACTION",
            status: 'loading'
        });
        expect(state).toBe(oldState);
    });
    it('search text change', () => {
        const state = usergroups(undefined, {
            type: SEARCHTEXTCHANGED,
            text: "TEXT"
        });
        expect(state.searchText).toBe("TEXT");
    });
    it('set loading', () => {
        const state = usergroups(undefined, {
            type: GETGROUPS,
            status: STATUS_LOADING
        });
        expect(state.status).toBe('loading');
    });
    it('get groups', () => {
        const state = usergroups(undefined, {
            type: GETGROUPS,
            status: STATUS_SUCCESS,
            groups: [],
            totalCount: 0
        });
        expect(state.groups).toExist();
        expect(state.groups.length).toBe(0);
    });
    it('edit group', () => {
        const state = usergroups(undefined, {
            type: EDITGROUP,
            group: {
                groupName: "group",
                description: "description"
            },
            totalCount: 0
        });
        expect(state.currentGroup).toExist();
        expect(state.currentGroup.groupName).toBe("group");
        const stateMerge = usergroups({currentGroup: {
            id: 1
        }}, {
            type: EDITGROUP,
            status: "success",
            group: {
                id: 1,
                groupName: "group",
                description: "description"
            },
            totalCount: 0
        });
        expect(stateMerge.currentGroup).toExist();
        expect(stateMerge.currentGroup.id).toBe(1);
        expect(stateMerge.currentGroup.groupName).toBe("group");

        // action for a user not related with current.
        let newState = usergroups(stateMerge, {
            type: EDITGROUP,
            status: STATUS_SUCCESS,
            group: {
                id: 2,
                groupName: "group",
                description: "description"
            },
            totalCount: 0
        });
        expect(newState).toBe(stateMerge);

    });

    it('edit group data', () => {
        const state = usergroups({currentGroup: {
            id: 1,
            groupName: "groupName"
        }}, {
            type: EDITGROUPDATA,
            key: "groupName",
            newValue: "newGroupName"
        });
        expect(state.currentGroup).toExist();
        expect(state.currentGroup.id).toBe(1);
        expect(state.currentGroup.groupName).toBe("newGroupName");
        const stateMerge = usergroups({currentGroup: {
            id: 1,
            groupName: "userName"
        }}, {
            type: EDITGROUPDATA,
            key: "description",
            newValue: "value2"
        });
        expect(stateMerge.currentGroup).toExist();
        expect(stateMerge.currentGroup.id).toBe(1);
        expect(stateMerge.currentGroup.description).toBe("value2");

        // edit existing data
        let stateMerge2 = usergroups(stateMerge, {
            type: EDITGROUPDATA,
            key: "description",
            newValue: "new description"
        });
        expect(stateMerge2.currentGroup).toExist();
        expect(stateMerge2.currentGroup.id).toBe(1);
        expect(stateMerge2.currentGroup.description).toBe("new description");
    });
    it('update group data', () => {
        const state = usergroups({currentGroup: {
            id: 1,
            groupName: "GroupName",
            users: [{id: 10, name: "user"}]
        }}, {
            id: 1,
            name: "GroupName",
            users: [{id: 10, name: "user"}],
            type: UPDATEGROUP,
            status: STATUS_SAVED
        });
        expect(state.currentGroup).toExist();
        expect(state.currentGroup.id).toBe(1);
        expect(state.currentGroup.users.length).toBe(1);
        expect(state.currentGroup.users[0].name).toBe("user");
    });

    it('delete usergroup', () => {
        const state = usergroups({groups: [{
            id: 1,
            groupName: "Group",
            users: []
        }]}, {
            type: DELETEGROUP,
            id: 1,
            status: "delete"
        });
        expect(state.deletingGroup).toExist();
        const cancelledState = usergroups(state, {
            type: DELETEGROUP,
            id: 1,
            status: "cancelled"
        });
        expect(cancelledState.deletingGroup).toBe(null);
    });

    it('get Available Users', () => {
        const state0 = usergroups({}, {
            type: SEARCHUSERS,
            status: STATUS_LOADING
        });
        expect(state0.availableUsersLoading).toBe(true);
        const state = usergroups({}, {
            type: SEARCHUSERS,
            users: [{name: "user1", id: 100}],
            status: STATUS_SUCCESS
        });
        expect(state.availableUsers).toExist();
        expect(state.availableUsers.length).toBe(1);
        expect(state.availableUsersLoading).toBe(false);
        const stateError = usergroups({}, {
            type: SEARCHUSERS,
            status: STATUS_ERROR,
            error: "ERROR"
        });
        expect(stateError.availableUsersError).toBe("ERROR");
        const stateUnchanged = usergroups(state0, {
            type: SEARCHUSERS,
            users: [{name: "user1", id: 100}],
            status: "STATUS_NOT_MANAGED"
        });
        expect(stateUnchanged).toBe(state0);
    });
});
