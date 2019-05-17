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

var InlineSpinner = require('../InlineSpinner');

describe('InlineSpinner', () => {
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
        const spinner = ReactDOM.render(<InlineSpinner />, document.getElementById("container"));
        expect(spinner).toExist();

        const domNode = ReactDOM.findDOMNode(spinner);
        expect(domNode).toExist();

        expect(domNode.style.display).toBe('none');
    });

    it('test loading animation', () => {
        const spinner = ReactDOM.render(<InlineSpinner loading/>, document.getElementById("container"));
        expect(spinner).toExist();

        const domNode = ReactDOM.findDOMNode(spinner);
        expect(domNode).toExist();

        expect(domNode.style.display).toBe('inline-block');
    });

});
