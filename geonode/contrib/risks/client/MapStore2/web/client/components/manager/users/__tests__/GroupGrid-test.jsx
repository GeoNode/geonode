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
var ReactTestUtils = require('react-addons-test-utils');
const GroupGrid = require('../GroupGrid');
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

describe("Test GroupGrid Component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('Test group grid rendering', () => {
        let comp = ReactDOM.render(
            <GroupGrid groups={[group1]}/>, document.getElementById("container"));
        expect(comp).toExist();
        comp = ReactDOM.render(
            <GroupGrid groups={[group1]} loading={true}/>, document.getElementById("container"));
        expect(comp).toExist();
        let domNode = ReactDOM.findDOMNode(comp);
        expect(domNode.className).toBe("container-fluid");
        let rows = ReactTestUtils.scryRenderedDOMComponentsWithClass(
          comp,
          "row"
        );
        expect(rows).toExist();
        expect(rows.length).toBe(2);
        let card = ReactTestUtils.scryRenderedDOMComponentsWithClass(comp, "gridcard");
        expect(card).toExist();
        expect(card.length).toBe(1);
        let buttons = ReactTestUtils.scryRenderedDOMComponentsWithClass(
          comp,
          "gridcard-button"
        );
        ReactTestUtils.Simulate.click(buttons[0]);
        ReactTestUtils.Simulate.click(buttons[1]);
        expect(buttons.length).toBe(2);
    });
    it('Test everyone\'s group rendering in grid', () => {
        let comp = ReactDOM.render(
            <GroupGrid groups={[{id: 999, groupName: "everyone"}]} loading={true}/>, document.getElementById("container"));
        expect(comp).toExist();
        let domNode = ReactDOM.findDOMNode(comp);
        expect(domNode.className).toBe("container-fluid");
        let buttons = ReactTestUtils.scryRenderedDOMComponentsWithClass(
          comp,
          "gridcard-button"
        );
        expect(buttons.length).toBe(0);
    });
    it('Test group grid events', () => {
        const testHandlers = {
            onEdit: () => {},
            onDelete: () => {}
        };
        const spyEdit = expect.spyOn(testHandlers, 'onEdit');
        const spyDelete = expect.spyOn(testHandlers, 'onDelete');
        let comp = ReactDOM.render(
            <GroupGrid groups={[group1]} onEdit={testHandlers.onEdit} onDelete={testHandlers.onDelete}/>, document.getElementById("container"));
        expect(comp).toExist();
        let domNode = ReactDOM.findDOMNode(comp);
        expect(domNode.className).toBe("container-fluid");
        let buttons = ReactTestUtils.scryRenderedDOMComponentsWithClass(
          comp,
          "gridcard-button"
        );
        expect(buttons.length).toBe(2);
        ReactTestUtils.Simulate.click(buttons[0]);
        ReactTestUtils.Simulate.click(buttons[1]);
        expect(spyEdit.calls.length).toEqual(1);
        expect(spyDelete.calls.length).toEqual(1);
    });

});
