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
var CRSSelector = require('../CRSSelector');

const TestUtils = require('react-addons-test-utils');

describe('CRSSelector', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('checks default', () => {

        const cmp = ReactDOM.render(<CRSSelector enabled={true}/>, document.getElementById("container"));
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        const select = cmpDom.getElementsByTagName("select").item(0);
        const opts = select.childNodes;
        expect(opts.length).toBeGreaterThan(3);

    });

    it('checks if a change of the combo fires the proper action', () => {
        let newCRS;
        const cmp = ReactDOM.render(<CRSSelector enabled={true} onCRSChange={ (crs) => {newCRS = crs; }}/>, document.getElementById("container"));
        const cmpDom = ReactDOM.findDOMNode(cmp);
        const select = cmpDom.getElementsByTagName("select").item(0);

        select.value = "EPSG:4326";
        TestUtils.Simulate.change(select, {target: {value: 'EPSG:4326'}});

        expect(newCRS).toBe('EPSG:4326');
    });
});
