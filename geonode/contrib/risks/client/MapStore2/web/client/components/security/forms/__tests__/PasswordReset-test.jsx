/**
 * Copyright 2015-2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const React = require('react');
const ReactDOM = require('react-dom');
const ReactTestUtils = require('react-addons-test-utils');
const PasswordReset = require('../PasswordReset');


describe("Test the password reset form component", () => {
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
        const cmp = ReactDOM.render(<PasswordReset/>, document.getElementById("container"));
        expect(cmp).toExist();
    });

    it('test component validity', () => {
        const cmp = ReactDOM.render(<PasswordReset />, document.getElementById("container"));
        expect(cmp).toExist();
        let password = ReactDOM.findDOMNode(ReactTestUtils.scryRenderedDOMComponentsWithTag(cmp, "input")[0]);
        expect(password).toExist();
        password.value = "test";
        ReactTestUtils.Simulate.change(password);
        expect(cmp.isValid()).toEqual(false);
        let password2 = ReactDOM.findDOMNode(ReactTestUtils.scryRenderedDOMComponentsWithTag(cmp, "input")[1]);
        expect(password2).toExist();
        password2.value = "test2";
        ReactTestUtils.Simulate.change(password2);
        expect(cmp.isValid()).toEqual(false);
        password2.value = "test";
        ReactTestUtils.Simulate.change(password2);
        // size is < then 6
        expect(cmp.isValid()).toEqual(false);

        // test valid
        password.value = "password";
        password2.value = "password";
        ReactTestUtils.Simulate.change(password);
        ReactTestUtils.Simulate.change(password2);
        expect(cmp.isValid()).toEqual(true);
    });
});
