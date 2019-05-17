/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const ReactDOM = require('react-dom');
const RuleAttributeSelect = require('../RuleAttributeSelect.jsx');
const expect = require('expect');

describe('test rule attribute select component', () => {

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
        const ruleAttributeSelect = ReactDOM.render(<RuleAttributeSelect/>, document.getElementById("container"));
        expect(ruleAttributeSelect).toExist();

        const dom = ReactDOM.findDOMNode(ruleAttributeSelect);
        expect(dom).toExist();

        const selects = dom.getElementsByClassName('Select-control');
        expect(selects.length).toBe(1);
    });
});
