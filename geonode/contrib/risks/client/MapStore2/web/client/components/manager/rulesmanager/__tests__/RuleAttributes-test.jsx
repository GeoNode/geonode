/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const ReactDOM = require('react-dom');
const RuleAttributes = require('../RuleAttributes.jsx');
const expect = require('expect');

describe('test rule attributes component', () => {

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
        const ruleAttributes = ReactDOM.render(<RuleAttributes/>, document.getElementById("container"));
        expect(ruleAttributes).toExist();

        const dom = ReactDOM.findDOMNode(ruleAttributes);
        expect(dom).toExist();

        const selects = dom.getElementsByClassName('Select-control');
        expect(selects.length).toBe(6);
    });
});
