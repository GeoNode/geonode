/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var GlobalSpinner = require('../GlobalSpinner');
var expect = require('expect');

describe('test the globalspinner component', () => {
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
        const globalspinner = ReactDOM.render(<GlobalSpinner/>, document.getElementById("container"));
        expect(globalspinner).toExist();
        const globalspinnerDiv = ReactDOM.findDOMNode(globalspinner);
        expect(globalspinnerDiv).toNotExist();
    });

    it('creates the component with layers loading and spinner to show', () => {
        const globalspinner = ReactDOM.render(<GlobalSpinner id="globalspinner" loading
            spinnersInfo={{globalspinner: true}}/>, document.getElementById("container"));
        expect(globalspinner).toExist();
        const globalspinnerDiv = ReactDOM.findDOMNode(globalspinner);
        expect(globalspinnerDiv).toExist();
    });

    it('creates the component with layers load', () => {
        const globalspinner = ReactDOM.render(<GlobalSpinner loading={false}/>, document.getElementById("container"));
        expect(globalspinner).toExist();
        const globalspinnerDiv = ReactDOM.findDOMNode(globalspinner);
        expect(globalspinnerDiv).toNotExist();
    });
});
