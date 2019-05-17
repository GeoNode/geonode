/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var HelpToggleBtn = require('../HelpToggleBtn');
var expect = require('expect');

describe('Test for HelpToggleBtn', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    // test DEFAULTS
    it('creates the component with defaults', () => {
        const helpToggleBtn = ReactDOM.render(<HelpToggleBtn/>, document.getElementById("container"));
        expect(helpToggleBtn).toExist();

        const helpToggleBtnDom = ReactDOM.findDOMNode(helpToggleBtn);
        expect(helpToggleBtnDom).toExist();

        const icons = helpToggleBtnDom.getElementsByTagName('span');
        expect(icons.length).toBe(1);

        expect(helpToggleBtnDom.className.indexOf('default') >= 0).toBe(true);
        expect(helpToggleBtnDom.innerHTML).toExist();
    });

    it('test button state', () => {
        const helpToggleBtn = ReactDOM.render(<HelpToggleBtn pressed/>, document.getElementById("container"));
        expect(helpToggleBtn).toExist();

        const helpToggleBtnDom = ReactDOM.findDOMNode(helpToggleBtn);

        expect(helpToggleBtnDom.className.indexOf('primary') >= 0).toBe(true);
    });

    it('test click handler calls right functions', () => {
        var triggered = 0;
        const clickFn = {
            changeHelpState: () => {triggered++; },
            changeHelpwinVisibility: () => {triggered++; }
        };
        // const spy = expect.spyOn(testHandlers, 'onClick');
        const helpToggleBtn = ReactDOM.render(<HelpToggleBtn
            pressed
            changeHelpState={clickFn.changeHelpState}
            changeHelpwinVisibility={clickFn.changeHelpwinVisibility}/>, document.getElementById("container"));

        const helpToggleBtnDom = ReactDOM.findDOMNode(helpToggleBtn);
        helpToggleBtnDom.click();

        expect(triggered).toEqual(2);
    });

});
