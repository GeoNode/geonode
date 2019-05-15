/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const React = require('react');
const ReactDOM = require('react-dom');
const ShareLink = require('../ShareLink');
const ReactTestUtils = require('react-addons-test-utils');

describe("The ShareLink component", () => {
    const url = location.href;

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('is created with defaults', () => {
        const cmpShareLink = ReactDOM.render(<ShareLink shareUrl={url}/>, document.getElementById("container"));
        expect(cmpShareLink).toExist();
    });

    it('should have the address url in the input field', () => {
        const cmpShareLink = ReactDOM.render(<ShareLink shareUrl={url}/>, document.getElementById("container"));
        expect(cmpShareLink).toExist();

        const inputDirectLink = ReactDOM.findDOMNode(ReactTestUtils.scryRenderedDOMComponentsWithTag(cmpShareLink, "input")[0]);
        expect(inputDirectLink).toExist();
        expect(inputDirectLink.value).toEqual(url);
    });

    it('should be selected when clicked', () => {
        const cmpShareLink = ReactDOM.render(<ShareLink shareUrl={url}/>, document.getElementById("container"));
        expect(cmpShareLink).toExist();

        const inputDirectLink = ReactDOM.findDOMNode(ReactTestUtils.scryRenderedDOMComponentsWithTag(cmpShareLink, "input")[0]);
        expect(inputDirectLink).toExist();

        ReactTestUtils.Simulate.focus(inputDirectLink);
        let selection = inputDirectLink.value.substring(inputDirectLink.selectionStart, inputDirectLink.selectionEnd);
        expect(selection).toEqual(url);
    });


});
