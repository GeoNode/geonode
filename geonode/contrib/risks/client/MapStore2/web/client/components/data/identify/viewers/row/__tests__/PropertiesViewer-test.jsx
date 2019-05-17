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
var PropertiesViewer = require('../PropertiesViewer');

describe('PropertiesViewer', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });
    it('test defaults', () => {
        const cmp = ReactDOM.render(<PropertiesViewer/>, document.getElementById("container"));
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        expect(cmpDom.childNodes.length).toBe(0);
    });
    it('test title rendering', () => {
        const cmp = ReactDOM.render(<PropertiesViewer title="testTitle"/>, document.getElementById("container"));
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        expect(cmpDom.childNodes.length).toBe(1);
        expect(cmpDom.childNodes.item(0).innerHTML).toBe("testTitle");
    });
    it('test body rendering', () => {
        const testProps = {
            k0: "v0",
            k1: "v1",
            k2: "v2"
        };
        const cmp = ReactDOM.render(<PropertiesViewer {...testProps}/>, document.getElementById("container"));
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        expect(cmpDom.childNodes.length).toBe(1);

        const body = cmpDom.childNodes.item(0);
        expect(body.childNodes.length).toBe(Object.keys(testProps).length);

        const testKeys = Object.keys(testProps);
        expect(Array.prototype.reduce.call(body.childNodes, (prev, child, i) => {
            let testKey = testKeys[i];
            let testVal = testProps[testKey];
            return prev
                && child.innerText === testKey + " " + testVal;
        }, true)).toBe(true);
    });

});
