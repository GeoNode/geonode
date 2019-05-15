/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require("react");
const expect = require('expect');
const ReactDOM = require('react-dom');
const UserGrid = require('../UserGrid');
const enabledUser = {
    id: 1,
    name: "USER1",
    role: "USER",
    enabled: true,
    groups: [{
        groupName: "GROUP1"
    }]
};
const disabledUser = {
    id: 2,
    name: "USER2",
    role: "USER",
    enabled: false,
    groups: [{
        groupName: "GROUP1"
    }]
};
const adminUser = {
    id: 3,
    name: "ADMIN",
    role: "ADMIN",
    enabled: true
};
const guestUser = {
    id: 4,
    name: "guest",
    role: "GUEST",
    enabled: true
};
describe("Test UserGrid Component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('Test users rendering', () => {
        let comp = ReactDOM.render(
            <UserGrid users={[enabledUser, disabledUser, adminUser]}/>, document.getElementById("container"));
        expect(comp).toExist();
        comp = ReactDOM.render(
            <UserGrid users={[enabledUser, disabledUser, adminUser]} loading={true}/>, document.getElementById("container"));
        expect(comp).toExist();
    });
    it('Test guestUser user', () => {
        let comp = ReactDOM.render(
            <UserGrid user={[guestUser]}/>, document.getElementById("container"));
        expect(comp).toExist();
    });
});
