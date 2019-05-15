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
var Font = require('../Font');

var ReactTestUtils = require('react-addons-test-utils');

const fonts = ['Font1', 'Font2'];

describe("Test the Font component", () => {
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
        const cmp = ReactDOM.render(<Font/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.childNodes.length).toBe(2);
        expect(node.childNodes[1].childNodes.length).toBe(4);
    });

    it('creates component with fonts', () => {
        const cmp = ReactDOM.render(<Font fonts={fonts}/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.getElementsByTagName('select')[0].childNodes.length).toBe(2);
        expect(node.getElementsByTagName('select')[0].childNodes[0].textContent).toBe('Font1');
    });

    it('launches onChangeFamily', () => {
        let called = false;

        const changeHandler = () => {
            called = true;
        };
        const cmp = ReactDOM.render(<Font onChangeFamily={changeHandler}/>, document.getElementById("container"));
        expect(cmp).toExist();
        const node = ReactDOM.findDOMNode(cmp);
        ReactTestUtils.Simulate.change(node.getElementsByTagName('select')[0]);

        expect(called).toBe(true);
    });

    it('launches onChangeSize', () => {
        let called = false;

        const changeHandler = () => {
            called = true;
        };
        const cmp = ReactDOM.render(<Font onChangeSize={changeHandler}/>, document.getElementById("container"));
        expect(cmp).toExist();
        const node = ReactDOM.findDOMNode(cmp);
        ReactTestUtils.Simulate.change(node.getElementsByTagName('input')[0]);

        expect(called).toBe(true);
    });

    it('launches onChangeBold', () => {
        let called = false;

        const changeHandler = () => {
            called = true;
        };
        const cmp = ReactDOM.render(<Font onChangeBold={changeHandler}/>, document.getElementById("container"));
        expect(cmp).toExist();
        const node = ReactDOM.findDOMNode(cmp);
        ReactTestUtils.Simulate.click(node.getElementsByTagName('button')[0]);

        expect(called).toBe(true);
    });

    it('launches onChangeItalic', () => {
        let called = false;

        const changeHandler = () => {
            called = true;
        };
        const cmp = ReactDOM.render(<Font onChangeItalic={changeHandler}/>, document.getElementById("container"));
        expect(cmp).toExist();
        const node = ReactDOM.findDOMNode(cmp);
        ReactTestUtils.Simulate.click(node.getElementsByTagName('button')[1]);

        expect(called).toBe(true);
    });
});
