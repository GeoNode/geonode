/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var React = require('react');
var ReactDOM = require('react-dom');
var Choice = require('../Choice');

var ReactTestUtils = require('react-addons-test-utils');

const items = [{
    name: 'A4'
}, {
    name: 'A3'
}];

describe("Test the Choice component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates component with defaults', () => {
        const cmp = ReactDOM.render(<Choice/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.childNodes.length).toBe(2);
        expect(node.childNodes[1].childNodes.length).toBe(0);
    });

    it('creates component with items', () => {
        const cmp = ReactDOM.render(<Choice items={items}/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.childNodes.length).toBe(2);
        expect(node.childNodes[1].childNodes.length).toBe(2);
        expect(node.childNodes[1].childNodes[0].textContent).toBe('A4');
        expect(node.childNodes[1].childNodes[1].textContent).toBe('A3');
    });

    it('launches onChange', () => {
        let called = false;

        const changeHandler = () => {
            called = true;
        };
        const cmp = ReactDOM.render(<Choice items={items} onChange={changeHandler}/>, document.getElementById("container"));
        expect(cmp).toExist();
        const node = ReactDOM.findDOMNode(cmp);
        ReactTestUtils.Simulate.change(node.childNodes[1]);

        expect(called).toBe(true);
    });
});
