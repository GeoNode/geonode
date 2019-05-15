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
var I18N = require('../I18N');
var Localized = require('../Localized');

var ita = {
    "locale": "it-IT",
    "messages": {
        "aboutLbl": "Info"
    }
};
var eng = {
    "locale": "en-US",
    "messages": {
        "aboutLbl": "About"
    }
};

describe('This test for I18N.Message', () => {
    const msgId = "aboutLbl";
    const data = {
        "en-US": eng,
        "it-IT": ita
    };
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('checks if the component renders english messages', () => {
        var currentData = data["en-US"];
        var testMsg = currentData.messages[msgId];

        const cmp = ReactDOM.render(<Localized messages={eng.messages} locale="en-US"><I18N.Message msgId={msgId}/></Localized>, document.getElementById("container"));
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();
        expect(cmpDom.innerHTML).toBe(testMsg);
    });

    it('checks if the component renders italian messages', () => {
        var currentData = data["it-IT"];
        var testMsg = currentData.messages[msgId];

        const cmp = ReactDOM.render(<Localized messages={ita.messages} locale="it-IT"><I18N.Message msgId={msgId}/></Localized>, document.getElementById("container"));
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();
        expect(cmpDom.innerHTML).toBe(testMsg);
    });
});
