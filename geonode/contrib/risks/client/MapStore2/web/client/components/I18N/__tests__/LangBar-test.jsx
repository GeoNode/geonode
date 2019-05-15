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
var LangBar = require('../LangBar');
var LocaleUtils = require('../../../utils/LocaleUtils');
const TestUtils = require('react-addons-test-utils');

describe('LangBar', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('checks default', () => {

        const cmp = ReactDOM.render(<LangBar/>, document.getElementById("container"));
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        const buttons = cmpDom.getElementsByTagName("button");

        expect(buttons.length === LocaleUtils.getSupportedLocales().length);

    });

    it('checks button click fires the proper action', () => {
        let newLang;
        const cmp = ReactDOM.render(<LangBar onLanguageChange={ (lang) => {newLang = lang; }}/>, document.getElementById("container"));
        const cmpDom = ReactDOM.findDOMNode(cmp);
        const select = cmpDom.getElementsByTagName("button").item(0);

        select.value = "it-IT";
        TestUtils.Simulate.click(select, {target: {value: 'it-IT'}});
        // select.children[1].click();

        expect(newLang).toBe('it-IT');
    });
});
