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
const UserTable = require('../UsersTable');
var ReactTestUtils = require('react-addons-test-utils');

const users = [{
    id: 2,
    name: "USER2",
    role: "USER",
    enabled: false,
    groups: [{
        groupName: "GROUP1"
    }]
 }, {
    id: 3,
    name: "ADMIN",
    role: "ADMIN",
    enabled: true
}];
describe("Test UsersTable Component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('Test usergroup table', () => {
        let comp = ReactDOM.render(
            <UserTable show={true} users={users}/>, document.getElementById("container"));
        expect(comp).toExist();
        let table = ReactTestUtils.scryRenderedDOMComponentsWithTag(comp, "table");
        expect(table.length).toBe(1);
        let rows = ReactTestUtils.scryRenderedDOMComponentsWithTag(comp, "tr");
        expect(rows.length).toBe(2);
    });
});
