/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var React = require('react');
var ReactDOM = require('react-dom');
var HtmlRenderer = require('../HtmlRenderer');

describe("This test for HtmlRenderer component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates componet with defaults', () => {
        const cmp = ReactDOM.render(<HtmlRenderer/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node.id).toNotExist();
        expect(node.childNodes.length).toBe(0);
    });

    it('creates empty componet with id', () => {
        const cmp = ReactDOM.render(<HtmlRenderer id="testId"/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node.id).toBe("testId");
        expect(node.childNodes.length).toBe(0);
    });

    it('creates a filled componet', () => {
        const srcCode = '<p id="innerP"><span id="innerSPAN">text</span></p>';
        const cmp = ReactDOM.render(<HtmlRenderer html={srcCode}/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node.childNodes.length).toBe(1);

        const innerP = node.childNodes[0];
        expect(innerP.id).toBe("innerP");
        expect(innerP.childNodes.length).toBe(1);

        const innerSPAN = innerP.childNodes[0];
        expect(innerSPAN.id).toBe("innerSPAN");
        expect(innerSPAN.innerHTML).toBe("text");
    });
});
