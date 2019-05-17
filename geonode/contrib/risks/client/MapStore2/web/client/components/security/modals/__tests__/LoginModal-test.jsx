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
const LoginForm = require('../LoginModal');

describe("Test the login modal", () => {
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
        const cmp = ReactDOM.render(<LoginForm options={{animation: false}}/>, document.getElementById("container"));
        expect(cmp).toExist();
    });

    it('creates empty component with error', () => {
        const cmp = ReactDOM.render(<LoginForm options={{animation: false}} show={true} loginError={{status: 0}}/>, document.getElementById("container"));
        expect(cmp).toExist();
        let node = document.getElementsByClassName('alert-danger');
        expect(node.length).toBe(1);
    });

    it('test component sumbit', () => {
        const testHandlers = {
            onSubmit: (user, password) => {
                return {user: user, password: password};
            },
            onLoginSuccess: () => {

            }
        };

        const spy = expect.spyOn(testHandlers, 'onSubmit');
        const spySuccess = expect.spyOn(testHandlers, 'onLoginSuccess');
        const cmp = ReactDOM.render(<LoginForm options={{animation: false}} show={true} key="test" onLoginSuccess={testHandlers.onLoginSuccess} onSubmit={testHandlers.onSubmit}/>, document.getElementById("container"));
        expect(cmp).toExist();
        let username = document.getElementsByTagName("input")[0];
        expect(username).toExist();
        username.value = "test";
        ReactTestUtils.Simulate.change(username);

        let password = document.getElementsByTagName("input")[1];
        expect(password).toExist();
        password.value = "test";
        ReactTestUtils.Simulate.change(password);

        let button = document.getElementsByTagName("button")[1];
        ReactTestUtils.Simulate.click(button);
        expect(spy.calls.length).toEqual(1);
        ReactDOM.render(<LoginForm options={{animation: false}} show={true} key="test" onSubmit={testHandlers.onSubmit} onLoginSuccess={testHandlers.onLoginSuccess} user={{name: "TEST"}} />, document.getElementById("container"));
        expect(spySuccess.calls.length).toEqual(1);


    });
});
