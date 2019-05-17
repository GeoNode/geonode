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
var Localized = require('../Localized');
var Message = require('../Message');
var HTML = require('../HTML');

const messages = {
    "testMsg": "my message"
};

describe('Test the localization support HOC', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('localizes wrapped Message component', () => {
        var localized = ReactDOM.render(
            <Localized locale="it-IT" messages={messages}>
                {() => <Message msgId="testMsg"/> }
            </Localized>
            , document.getElementById("container"));
        var dom = ReactDOM.findDOMNode(localized);
        expect(dom).toExist();
        expect(dom.innerHTML).toBe("my message");
    });

    it('localizes wrapped HTML component', () => {
        var localized = ReactDOM.render(
            <Localized locale="it-IT" messages={messages}>
                {() => <HTML msgId="testMsg"/> }
            </Localized>
            , document.getElementById("container"));
        var dom = ReactDOM.findDOMNode(localized);
        expect(dom).toExist();
        expect(dom.innerHTML).toBe("my message");
    });

    it('tests localized component without messages', () => {
        var localized = ReactDOM.render(
            <Localized locale="it-IT">
                {() => <HTML msgId="testMsg"/> }
            </Localized>
            , document.getElementById("container"));
        var dom = ReactDOM.findDOMNode(localized);
        expect(dom).toNotExist();
    });

    it('renders a loading error', () => {
        var localized = ReactDOM.render(<Localized loadingError="loadingError" />, document.getElementById("container"));
        var dom = ReactDOM.findDOMNode(localized);
        expect(dom).toExist();
        expect(dom.className.indexOf("loading-locale-error")).toNotBe(-1);
    });
});
