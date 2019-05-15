/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const ReactDOM = require('react-dom');
const RulesFilterPanel = require('../RulesFiltersPanel.jsx');
const expect = require('expect');

describe('test rules filters panel component', () => {

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
        const rulesFilterPanel = ReactDOM.render(<RulesFilterPanel/>, document.getElementById("container"));
        expect(rulesFilterPanel).toExist();

        const dom = ReactDOM.findDOMNode(rulesFilterPanel);
        expect(dom).toExist();

        const selects = dom.getElementsByClassName('Select-control');
        expect(selects.length).toBe(6);

        const panelBody = dom.getElementsByClassName('panel-body');
        expect(panelBody.length).toBe(1);
    });
});
