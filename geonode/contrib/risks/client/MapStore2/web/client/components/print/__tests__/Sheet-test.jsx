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
var Sheet = require('../Sheet');

var ReactTestUtils = require('react-addons-test-utils');

const layouts = [{
    name: 'A4'
}, {
    name: 'A4_landscape'
}, {
    name: 'A3'
}, {
    name: 'A3_landscape'
}];

const weirdLayouts = [{
    name: 'my_A4'
}, {
    name: 'yours_A4_landscape'
}];

describe("Test the Sheet component", () => {
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
        const cmp = ReactDOM.render(<Sheet/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.childNodes.length).toBe(2);
        expect(node.childNodes[1].childNodes.length).toBe(0);
    });

    it('creates component with layouts', () => {
        const cmp = ReactDOM.render(<Sheet layouts={layouts}/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.childNodes.length).toBe(2);
        expect(node.childNodes[1].childNodes.length).toBe(2);
        expect(node.childNodes[1].childNodes[0].textContent).toBe('A4');
        expect(node.childNodes[1].childNodes[1].textContent).toBe('A3');
    });

    it('creates component with regex', () => {
        const cmp = ReactDOM.render(<Sheet layouts={weirdLayouts} sheetRegex={/^[^_]+_([^_]+)/}/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.childNodes.length).toBe(2);
        expect(node.childNodes[1].childNodes.length).toBe(1);
        expect(node.childNodes[1].childNodes[0].textContent).toBe('A4');
    });

    it('launches onChange', () => {
        let called = false;

        const changeHandler = () => {
            called = true;
        };
        const cmp = ReactDOM.render(<Sheet layouts={layouts} onChange={changeHandler}/>, document.getElementById("container"));
        expect(cmp).toExist();
        const node = ReactDOM.findDOMNode(cmp);
        ReactTestUtils.Simulate.change(node.childNodes[1]);

        expect(called).toBe(true);
    });

    it('uses custom layoutNames', () => {
        const layoutNames = {
            'A4': 'L1',
            'A3': 'L2'
        };
        const cmp = ReactDOM.render(<Sheet layouts={layouts} layoutNames={layoutNames}/>, document.getElementById("container"));
        expect(cmp).toExist();
        const node = ReactDOM.findDOMNode(cmp);
        const options = node.getElementsByTagName('option');
        expect(options.length).toBe(2);
        expect(options[0].innerHTML).toBe('L1');
        expect(options[1].innerHTML).toBe('L2');

    });

    it('uses custom layoutNames function', () => {
        const layoutNames = (layout) => layout + " sheet";
        const cmp = ReactDOM.render(<Sheet layouts={layouts} layoutNames={layoutNames}/>, document.getElementById("container"));
        expect(cmp).toExist();
        const node = ReactDOM.findDOMNode(cmp);
        const options = node.getElementsByTagName('option');
        expect(options.length).toBe(2);
        expect(options[0].innerHTML).toBe('A4 sheet');
        expect(options[1].innerHTML).toBe('A3 sheet');

    });
});
