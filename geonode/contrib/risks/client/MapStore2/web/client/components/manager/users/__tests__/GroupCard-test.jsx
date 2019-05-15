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
const GroupCard = require('../GroupCard');
var ReactTestUtils = require('react-addons-test-utils');
const group1 = {
    id: 1,
    groupName: "GROUP1",
    description: "description",
    enabled: true,
    users: [{
        name: "USER1",
        id: 100
    }]
};

describe("Test GroupCard Component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('Test group rendering', () => {
        let comp = ReactDOM.render(
            <GroupCard group={group1}/>, document.getElementById("container"));
        expect(comp).toExist();
        let title = ReactTestUtils.scryRenderedDOMComponentsWithClass(
              comp,
              "gridcard-title"
        );
        expect(title.length).toBe(1);
        expect(ReactTestUtils.scryRenderedDOMComponentsWithClass(
          comp,
          "group-thumb-description"
        ).length).toBe(1);
    });
});
