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
const PseudoColorSettings = require('../PseudoColorSettings');

describe("Test the PseudoColorSettings component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates component with defaults', () => {
        const cmp = ReactDOM.render(<PseudoColorSettings/>, document.getElementById("container"));
        expect(cmp).toExist();
    });

    it('creates component add entry', () => {
        const cmp = ReactDOM.render(<PseudoColorSettings />, document.getElementById("container"));
        expect(cmp).toExist();
        cmp.addEntry();
    });
    it('creates component remove entry', () => {
        const cmp = ReactDOM.render(<PseudoColorSettings selected={0} colorMapEntry={[{color: '#AA34FF', quantity: 1, label: "test" }]}/>, document.getElementById("container"));
        expect(cmp).toExist();
        cmp.removeEntry();
        cmp.selectEntry(2);
    });

});
