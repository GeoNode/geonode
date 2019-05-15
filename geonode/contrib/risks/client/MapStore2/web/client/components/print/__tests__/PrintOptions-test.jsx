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
var PrintOptions = require('../PrintOptions');

const layouts = [{
    name: 'A4'
}, {
    name: 'A4_landscape'
}, {
    name: 'A3'
}, {
    name: 'A3_landscape'
}];

const options = [{label: "O1", value: "O1"}, {label: "O2", value: "O2"}];

describe("Test the PrintOptions component", () => {
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
        const cmp = ReactDOM.render(<PrintOptions/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.getElementsByTagName('input').length).toBe(2);
        expect(node.getElementsByTagName('input')[0].checked).toBe(true);
        expect(node.getElementsByTagName('input')[1].checked).toBe(false);
    });

    it('creates component with value', () => {
        const cmp = ReactDOM.render(<PrintOptions selected="Option2"/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.getElementsByTagName('input').length).toBe(2);
        expect(node.getElementsByTagName('input')[0].checked).toBe(false);
        expect(node.getElementsByTagName('input')[1].checked).toBe(true);
    });

    it('creates component with options', () => {
        const cmp = ReactDOM.render(<PrintOptions options={options}/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.getElementsByTagName('input').length).toBe(2);
        expect(node.getElementsByTagName('input')[0].value).toBe('O1');
        expect(node.getElementsByTagName('input')[1].value).toBe('O2');
    });

    it('creates component enabled', () => {
        const cmp = ReactDOM.render(<PrintOptions enableRegex={/landscape/} layouts={layouts}/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.getElementsByTagName('input').length).toBe(2);
        expect(node.getElementsByTagName('input')[0].disabled).toBe(false);
        expect(node.getElementsByTagName('input')[1].disabled).toBe(false);
    });

    it('creates component disabled', () => {
        const cmp = ReactDOM.render(<PrintOptions enableRegex={/fake/} layouts={layouts}/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.getElementsByTagName('input').length).toBe(2);
        expect(node.getElementsByTagName('input')[0].disabled).toBe(true);
        expect(node.getElementsByTagName('input')[1].disabled).toBe(true);
    });
});
