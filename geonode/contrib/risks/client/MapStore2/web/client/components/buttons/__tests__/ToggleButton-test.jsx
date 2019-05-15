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
var ToggleButton = require('../ToggleButton');

describe("test the ToggleButton", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('test default properties', () => {
        const tb = ReactDOM.render(<ToggleButton/>, document.getElementById("container"));
        expect(tb).toExist();

        const tbNode = ReactDOM.findDOMNode(tb);
        expect(tbNode).toExist();
        expect(tbNode.id).toNotExist();

        expect(tbNode).toExist();
        expect(tbNode.className.indexOf('default') >= 0).toBe(true);
        expect(tbNode.innerHTML).toNotExist();
    });

    it('test glyphicon property', () => {
        const tb = ReactDOM.render(<ToggleButton glyphicon="info-sign"/>, document.getElementById("container"));
        expect(tb).toExist();

        const tbNode = ReactDOM.findDOMNode(tb);
        expect(tbNode).toExist();
        expect(tbNode).toExist();
        const icons = tbNode.getElementsByTagName('span');
        expect(icons.length).toBe(1);
    });

    it('test glyphicon property with text', () => {
        const tb = ReactDOM.render(<ToggleButton glyphicon="info-sign" text="button"/>, document.getElementById("container"));
        expect(tb).toExist();

        const tbNode = ReactDOM.findDOMNode(tb);
        expect(tbNode).toExist();
        expect(tbNode).toExist();

        const btnItems = tbNode.getElementsByTagName('span');
        expect(btnItems.length).toBe(1);
        expect(tbNode.innerText.indexOf("button") !== -1).toBe(true);
    });

    it('test button state', () => {
        const tb = ReactDOM.render(<ToggleButton pressed/>, document.getElementById("container"));
        expect(tb).toExist();

        const tbNode = ReactDOM.findDOMNode(tb);

        expect(tbNode.className.indexOf('primary') >= 0).toBe(true);
    });

    it('test click handler', () => {

        let genericTest = function(btnType) {
            const testHandlers = {
                onClick: (pressed) => {return pressed; }
            };
            const spy = expect.spyOn(testHandlers, 'onClick');
            const tb = ReactDOM.render(<ToggleButton pressed onClick={testHandlers.onClick} btnType={btnType}/>, document.getElementById("container"));

            const tbNode = ReactDOM.findDOMNode(tb);
            tbNode.click();

            expect(spy.calls.length).toEqual(1);
            expect(spy.calls[0].arguments).toEqual([false]);
        };

        genericTest('normal');
        genericTest('image');
    });

    it('test image button', () => {
        const tb = ReactDOM.render(<ToggleButton btnType={'image'}/>, document.getElementById("container"));
        expect(tb).toExist();
        const tbNode = ReactDOM.findDOMNode(tb);
        expect(tbNode.localName).toBe("img");
    });
});
