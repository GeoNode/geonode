 /**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactDOM = require('react-dom');
const SharingLink = require('../SharingLink');
const Localized = require('../../I18N/Localized');
const expect = require('expect');

const TestUtils = require('react-addons-test-utils');

describe('Tests for SharingLink', () => {

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('create the component with defaults', () => {
        const component = ReactDOM.render(<SharingLink/>, document.getElementById('container'));
        expect(component).toExist();
        // no dom node should be rendered with the default values
        const componentDom = ReactDOM.findDOMNode(component);
        expect(componentDom).toNotExist();
    });

    it('create the component with required url property', () => {
        const component = ReactDOM.render(<SharingLink url="url"/>, document.getElementById('container'));
        expect(component).toExist();
        // expecting a dom node to be available
        const componentDom = ReactDOM.findDOMNode(component);
        expect(componentDom).toExist();
        // we should have an input and a button available
        const input = TestUtils.findRenderedDOMComponentWithTag(component, 'input');
        expect(input).toExist();
        expect(input.value).toBe('url');
        const button = TestUtils.findRenderedDOMComponentWithTag(component, 'button');
        expect(button).toExist();
    });

    it('create the component with a valid label id', () => {
        // creating the messages object
        const messages = {'link': 'Link'};
        // intanciating the component
        const component = ReactDOM.render(<Localized locale="en-US" messages={messages}><SharingLink url="url" labelId="link"/></Localized>,
            document.getElementById('container'));
        expect(component).toExist();
        // expecting a dom node to be available
        const componentDom = ReactDOM.findDOMNode(component);
        expect(componentDom).toExist();
        // we should have an input and a button available
        const input = TestUtils.findRenderedDOMComponentWithTag(component, 'input');
        expect(input).toExist();
        expect(input.value).toBe('url');
        const button = TestUtils.findRenderedDOMComponentWithTag(component, 'button');
        expect(button).toExist();
        const buttonText = button.innerText || button.textContent;
        expect(buttonText).toExist();
        expect(buttonText.indexOf('Link')).toBeGreaterThan(-1);
    });

    it('copy button click', () => {
        // creating a copy to clipboard callback to spy on
        const actions = {
            onCopy: () => {}
        };
        const spy = expect.spyOn(actions, "onCopy");
        // intanciate the main component
        const component = ReactDOM.render(<SharingLink url="url" onCopy={actions.onCopy}/>, document.getElementById('container'));
        expect(component).toExist();
        // if propmt for ctrl+c we accept
        expect.spyOn(window, 'prompt').andReturn(true);
        // testing that on copy call back is invoked
        const button = TestUtils.findRenderedDOMComponentWithTag(component, 'button');
        expect(button).toExist();
        button.click();
        expect(spy.calls.length).toBe(1);
    });
});
