/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const ReactDOM = require('react-dom');
const RulesManager = require('../RulesManager.jsx');
const expect = require('expect');

describe('test rules manager component', () => {

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
        const rulesManager = ReactDOM.render(<RulesManager/>, document.getElementById("container"));
        expect(rulesManager).toExist();

        const dom = ReactDOM.findDOMNode(rulesManager);
        expect(dom).toExist();

        const panelBody = dom.getElementsByClassName('panel-body');
        expect(panelBody.length).toBe(2);
    });
});
