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
const BandSelector = require('../BandSelector');

describe("Test the BandSelector component", () => {
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
        const cmp = ReactDOM.render(<BandSelector/>, document.getElementById("container"));
        expect(cmp).toExist();
        cmp.props.onChange();
    });

    it('creates component contrast', () => {
        const cmp = ReactDOM.render(<BandSelector contrast="GammaValue" disabled={true}/>, document.getElementById("container"));
        expect(cmp).toExist();
    });
    it('creates component algorithm', () => {
        const cmp = ReactDOM.render(<BandSelector contrast="Normalize" algorithm="" disabled={true}/>, document.getElementById("container"));
        expect(cmp).toExist();
    });

});
