/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactDOM = require('react-dom');
const expect = require('expect');

const PaginationToolbar = require('../PaginationToolbar');

describe('PaginationToolbar', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    // test DEFAULTS
    it('creates the component with defaults', () => {
        const item = ReactDOM.render(<PaginationToolbar />, document.getElementById("container"));
        expect(item).toExist();
    });


    // test items
    it('creates the component with items', () => {
        const item = ReactDOM.render(<PaginationToolbar pageSize={2} page={1} items={["a", "b"]} total={2}/>, document.getElementById("container"));
        expect(item).toExist();
        const pagination = ReactDOM.findDOMNode(item).getElementsByClassName("pagination");
        expect(pagination).toExist();
        expect(pagination.length).toBe(1);
        const buttons = pagination[0].getElementsByTagName('a');
        expect(buttons).toExist();
        expect(buttons.length).toBe(5); // current page + prev, next...
    });
    // test loading
    it('creates the component loading', () => {
        const item = ReactDOM.render(<PaginationToolbar pageSize={2} page={1} items={["a", "b"]} total={2} loading={true} />, document.getElementById("container"));
        expect(item).toExist();
        const spinner = ReactDOM.findDOMNode(item).getElementsByClassName('spinner');
        expect(spinner).toExist();
        expect(spinner.length).toBe(1);
    });
});
