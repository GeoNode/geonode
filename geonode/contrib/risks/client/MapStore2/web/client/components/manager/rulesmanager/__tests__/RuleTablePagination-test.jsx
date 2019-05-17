/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const ReactDOM = require('react-dom');
const RulesTablePagination = require('../RulesTablePagination.jsx');
const expect = require('expect');

describe('test rules table pagination component', () => {

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates the component with defaults', () => {
        const rulesTablePagination = ReactDOM.render(<RulesTablePagination/>, document.getElementById("container"));
        expect(rulesTablePagination).toExist();

        const dom = ReactDOM.findDOMNode(rulesTablePagination);
        expect(dom).toExist();

        const pagination = dom.getElementsByClassName('pagination');
        expect(pagination.length).toBe(1);
    });
});
