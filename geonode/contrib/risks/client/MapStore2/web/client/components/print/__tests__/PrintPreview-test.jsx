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
var PrintPreview = require('../PrintPreview');

var ReactTestUtils = require('react-addons-test-utils');

window.PDFJS = {
    getDocument: () => ({
        then: (callback) => {
            callback.call(null, {
                numPages: 10,
                getPage: () => ({
                    then: (cb) => {
                        cb.call(null);
                    }
                })
            });
        }
    })
};

describe("Test the PrintPreview component", () => {
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
        const cmp = ReactDOM.render(<PrintPreview/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
    });

    it('pdf next page', (done) => {
        const handler = (page) => {
            expect(page).toBe(2);
            done();
        };
        const cmp = ReactDOM.render(<PrintPreview pages={10} currentPage={1} setPage={handler} url=""/>, document.getElementById("container"));
        expect(cmp).toExist();
        const node = ReactDOM.findDOMNode(cmp);
        ReactTestUtils.Simulate.click(node.getElementsByTagName('button')[5]);
    });

    it('pdf last page', (done) => {
        const handler = (page) => {
            expect(page).toBe(9);
            done();
        };
        const cmp = ReactDOM.render(<PrintPreview pages={10} currentPage={1} setPage={handler} url=""/>, document.getElementById("container"));
        expect(cmp).toExist();
        const node = ReactDOM.findDOMNode(cmp);
        ReactTestUtils.Simulate.click(node.getElementsByTagName('button')[6]);
    });

    it('pdf first page', (done) => {
        const handler = (page) => {
            expect(page).toBe(0);
            done();
        };
        const cmp = ReactDOM.render(<PrintPreview pages={10} currentPage={10} setPage={handler} url=""/>, document.getElementById("container"));
        expect(cmp).toExist();
        const node = ReactDOM.findDOMNode(cmp);
        ReactTestUtils.Simulate.click(node.getElementsByTagName('button')[3]);
    });

    it('pdf prev page', (done) => {
        const handler = (page) => {
            expect(page).toBe(9);
            done();
        };
        const cmp = ReactDOM.render(<PrintPreview pages={10} currentPage={10} setPage={handler} url=""/>, document.getElementById("container"));
        expect(cmp).toExist();
        const node = ReactDOM.findDOMNode(cmp);
        ReactTestUtils.Simulate.click(node.getElementsByTagName('button')[4]);
    });

    it('pdf zoom in', (done) => {
        const handler = (scale) => {
            expect(scale).toBe(2.0);
            done();
        };
        const cmp = ReactDOM.render(<PrintPreview zoomFactor={2.0} scale={1.0}
            pages={10} currentPage={1} setScale={handler} url=""/>, document.getElementById("container"));
        expect(cmp).toExist();
        const node = ReactDOM.findDOMNode(cmp);
        ReactTestUtils.Simulate.click(node.getElementsByTagName('button')[1]);
    });

    it('pdf zoom out', (done) => {
        const handler = (scale) => {
            expect(scale).toBe(2.0);
            done();
        };
        const cmp = ReactDOM.render(<PrintPreview zoomFactor={2.0} scale={4.0}
            pages={10} currentPage={1} setScale={handler} url=""/>, document.getElementById("container"));
        expect(cmp).toExist();
        const node = ReactDOM.findDOMNode(cmp);
        ReactTestUtils.Simulate.click(node.getElementsByTagName('button')[2]);
    });
});
