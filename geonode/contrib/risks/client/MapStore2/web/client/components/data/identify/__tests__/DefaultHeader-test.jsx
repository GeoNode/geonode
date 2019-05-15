/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactDOM = require('react-dom');

const DefaultHeader = require('../DefaultHeader.jsx');

const expect = require('expect');

describe('DefaultHeader', () => {

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates the DefaultHeader component with defaults', () => {
        const header = ReactDOM.render(
            <DefaultHeader/>,
            document.getElementById("container")
        );

        expect(header).toExist();
    });

    it('creates the DefaultHeader component with title', () => {
        const header = ReactDOM.render(
            <DefaultHeader title="mytitle"/>,
            document.getElementById("container")
        );

        expect(header).toExist();
        const dom = ReactDOM.findDOMNode(header);
        expect(dom.innerHTML.indexOf('mytitle') !== -1).toBe(true);
    });
});
