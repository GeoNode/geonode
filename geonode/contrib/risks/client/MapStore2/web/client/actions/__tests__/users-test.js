/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const assign = require('object-assign');
const {
    USERMANAGER_GETUSERS,
    getUsers,
    editUser, USERMANAGER_EDIT_USER,
    changeUserMetadata, USERMANAGER_EDIT_USER_DATA,
    saveUser, USERMANAGER_UPDATE_USER,
    deleteUser, USERMANAGER_DELETE_USER
} = require('../users');
let GeoStoreDAO = require('../../api/GeoStoreDAO');
let oldAddBaseUri = GeoStoreDAO.addBaseUrl;

describe('Test correctness of the users actions', () => {
    beforeEach(() => {
        GeoStoreDAO.addBaseUrl = (options) => {
            return assign(options, {baseURL: 'base/web/client/test-resources/geostore/'});
        };
    });

    afterEach(() => {
        GeoStoreDAO.addBaseUrl = oldAddBaseUri;
    });
    it('getUsers', (done) => {
        const retFun = getUsers('users.json', {params: {start: 0, limit: 10}});
        expect(retFun).toExist();
        let count = 0;
        retFun((action) => {
            expect(action.type).toBe(USERMANAGER_GETUSERS);
            count++;
            if (count === 2) {
                expect(action.users).toExist();
                expect(action.users[0]).toExist();
                expect(action.users[0].groups).toExist();
                done();
            }

        });

    });
    it('getUsers with old search', (done) => {
        const retFun = getUsers();
        expect(retFun).toExist();
        let count = 0;
        retFun((action) => {
            expect(action.type).toBe(USERMANAGER_GETUSERS);
            count++;
            if (count === 2) {
                expect(action.users).toExist();
                expect(action.users[0]).toExist();
                expect(action.users[0].groups).toExist();
                done();
            }

        }, () => ({users: { searchText: "users.json"}}));

    });

    it('getUsers error', (done) => {
        const retFun = getUsers('MISSING_LINK', {params: {start: 0, limit: 10}});
        expect(retFun).toExist();
        let count = 0;
        retFun((action) => {
            expect(action.type).toBe(USERMANAGER_GETUSERS);
            count++;
            if (count === 2) {
                expect(action.error).toExist();
                done();
            }

        });

    });

    it('getUsers issue returning empty response', (done) => {
        const retFun = getUsers('empty.json', {params: {start: 0, limit: 10}});
        expect(retFun).toExist();
        let count = 0;
        retFun((action) => {
            expect(action.type).toBe(USERMANAGER_GETUSERS);
            count++;
            if (count === 2) {
                expect(action).toExist();
                done();
            }

        });

    });

    it('editUser', (done) => {
        const retFun = editUser({id: 1});
        expect(retFun).toExist();
        let count = 0;
        retFun((action) => {
            expect(action.type).toBe(USERMANAGER_EDIT_USER);
            count++;
            if (count === 2) {
                expect(action.user).toExist();
                expect(action.status).toBe("success");
                done();
            }
        });
    }, {security: {user: {role: "ADMIN"}}});
    it('editUser with empty string groups', (done) => {
        const retFun = editUser({id: 2});
        expect(retFun).toExist();
        let count = 0;
        retFun((action) => {
            expect(action.type).toBe(USERMANAGER_EDIT_USER);
            count++;
            if (count === 2) {
                expect(action.user).toExist();
                expect(action.status).toBe("success");
                done();
            }
        });
    });

    it('editUser new', (done) => {
        let template = {name: "hello"};
        const retFun = editUser(template);
        expect(retFun).toExist();
        let count = 0;
        retFun((action) => {
            expect(action.type).toBe(USERMANAGER_EDIT_USER);
            count++;
            if (count === 1) {
                expect(action.user).toExist();
                expect(action.user).toBe(template);
                done();
            }
        });
    });

    it('editUser error', (done) => {
        const retFun = editUser({id: 99999});
        expect(retFun).toExist();
        let count = 0;
        retFun((action) => {
            expect(action.type).toBe(USERMANAGER_EDIT_USER);
            count++;
            if (count === 2) {
                expect(action.error).toExist();
                expect(action.status).toBe("error");
                done();
            }
        });
    });
    it('change user metadata', () => {
        const action = changeUserMetadata("name", "newName");
        expect(action).toExist();
        expect(action.type).toBe(USERMANAGER_EDIT_USER_DATA);
        expect(action.key).toBe("name");
        expect(action.newValue).toBe("newName");

    });
    it('saveUser update', (done) => {
        const retFun = saveUser({id: 1});
        expect(retFun).toExist();
        let count = 0;
        retFun((action) => {
            expect(action.type).toBe(USERMANAGER_UPDATE_USER);
            count++;
            if (count === 2) {
                expect(action.user).toExist();
                expect(action.status).toBe("saved");
                done();
            }
        });
    });
    it('saveUser create', (done) => {
        GeoStoreDAO.addBaseUrl = (options) => {
            return assign(options, {baseURL: 'base/web/client/test-resources/geostore/users/newUser.txt#'});
        };
        const retFun = saveUser({name: "test", role: "USER", password: "password"});
        expect(retFun).toExist();
        let count = 0;
        retFun((action) => {
            expect(action.type).toBe(USERMANAGER_UPDATE_USER);
            count++;
            if (count === 2) {
                expect(action.user).toExist();
                expect(action.user.id).toExist();
                expect(action.status).toBe("created");
                done();
            }
        });
    });
    it('saveUser create with groups', (done) => {
        GeoStoreDAO.addBaseUrl = (options) => {
            return assign(options, {baseURL: 'base/web/client/test-resources/geostore/users/newUser.txt#'});
        };
        const retFun = saveUser({name: "test", groups: [{groupName: "everyone"}, {groupName: "testers"}], role: "USER", password: "password"});
        expect(retFun).toExist();
        let count = 0;
        retFun((action) => {
            expect(action.type).toBe(USERMANAGER_UPDATE_USER);
            count++;
            if (count === 2) {
                expect(action.user).toExist();
                expect(action.user.id).toExist();
                expect(action.user.groups).toExist();
                expect(action.user.groups.length).toBe(2);
                done();
            }
        });
    });
    it('saveUser error', (done) => {
        const retFun = saveUser({id: 3});
        expect(retFun).toExist();
        let count = 0;
        retFun((action) => {
            expect(action.type).toBe(USERMANAGER_UPDATE_USER);
            count++;
            if (count === 2) {
                expect(action.user).toExist();
                expect(action.status).toBe("error");
                done();
            }
        });
    });
    it('deleteUser', (done) => {
        let confirm = deleteUser(1);
        expect(confirm).toExist();
        expect(confirm.status).toBe("confirm");
        const retFun = deleteUser(1, "delete");
        expect(retFun).toExist();
        let count = 0;
        retFun((action) => {
            expect(action.type).toBe(USERMANAGER_DELETE_USER);
            count++;
            if (count === 2) {
                expect(action.status).toExist();
                expect(action.id).toBe(1);
                done();
            }
        });
    });

});
