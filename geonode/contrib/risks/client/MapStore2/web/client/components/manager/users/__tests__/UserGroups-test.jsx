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
const UserGroups = require('../UserGroups');
const user1 = {
    id: 1,
    name: "USER1",
    role: "USER",
    enabled: true,
    groups: [{
        id: 10,
        groupName: "everyone"
    }, {
        id: 11,
        groupName: "GROUP1"
    }]
};

const groups = [{
    id: 10,
    groupName: "everyone"
}, {
    id: 11,
    groupName: "GROUP1"
}, {
    id: 12,
    groupName: "GROUP2"
}];

describe("Test UserGroups Component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('Test rendering for existing user', () => {
        let comp = ReactDOM.render(
            <UserGroups user={user1} groups={groups}/>, document.getElementById("container"));
        expect(comp).toExist();
        comp.onChange([{value: 10, groupName: "everyone"}]);
    });
    it('Test rendering for new user', () => {
        let comp = ReactDOM.render(
            <UserGroups groups={groups}/>, document.getElementById("container"));
        expect(comp).toExist();
        expect(comp.getOptions()).toExist();
        expect(comp.getOptions().length).toBe(groups.length);

        expect(comp.getDefaultGroups()).toExist();
        expect(comp.getDefaultGroups().length).toBe(1);
        expect(comp.getDefaultGroups()[0].groupName).toBe("everyone");
    });
});
