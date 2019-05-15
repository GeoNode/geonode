/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactDOM = require('react-dom');
const ReactTestUtils = require('react-addons-test-utils');

const SwipeHeader = require('../SwipeHeader.jsx');

const expect = require('expect');

describe('SwipeHeader', () => {

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates the SwipeHeader component with defaults', () => {
        const header = ReactDOM.render(
            <SwipeHeader/>,
            document.getElementById("container")
        );

        expect(header).toExist();
    });

    it('creates the SwipeHeader component with title', () => {
        const header = ReactDOM.render(
            <SwipeHeader title="mytitle"/>,
            document.getElementById("container")
        );

        expect(header).toExist();
        const dom = ReactDOM.findDOMNode(header);
        expect(dom.innerHTML.indexOf('mytitle') !== -1).toBe(true);
    });

    it('creates the SwipeHeader component with swipe buttons', () => {
        const header = ReactDOM.render(
            <SwipeHeader title="mytitle"/>,
            document.getElementById("container")
        );

        expect(header).toExist();
        const dom = ReactDOM.findDOMNode(header);
        expect(dom.getElementsByTagName('button').length).toBe(2);
    });

    it('calls containers handler when swipe buttons are pressed', () => {
        const testHandlers = {
            onNext: () => {},
            onPrevious: () => {}
        };

        const container = () => ({
            swipe: testHandlers
        });

        const spyNext = expect.spyOn(testHandlers, 'onNext');
        const spyPrev = expect.spyOn(testHandlers, 'onPrevious');

        const header = ReactDOM.render(
            <SwipeHeader title="mytitle" container={container} onNext={testHandlers.onNext} onPrevious={testHandlers.onPrevious}/>,
            document.getElementById("container")
        );
        const dom = ReactDOM.findDOMNode(header);
        const buttons = dom.getElementsByTagName('button');

        ReactTestUtils.Simulate.click(buttons[0]);
        expect(spyPrev.calls.length).toEqual(1);
        ReactTestUtils.Simulate.click(buttons[1]);
        expect(spyNext.calls.length).toEqual(1);
    });
});
