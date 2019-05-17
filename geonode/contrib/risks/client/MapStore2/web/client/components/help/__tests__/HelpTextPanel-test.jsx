/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var HelpTextPanel = require('../HelpTextPanel');
var expect = require('expect');

describe('Test for HelpTextPanel', () => {
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
        const helpPanel = ReactDOM.render(<HelpTextPanel asPanel/>, document.getElementById("container"));
        expect(helpPanel).toExist();

        const helpPanelDom = ReactDOM.findDOMNode(helpPanel);
        expect(helpPanelDom).toExist();
        // expect(helpPanelDom.id).toExist();
        expect(helpPanelDom.className.indexOf('hidden') >= 0).toBe(true);

        // header text
        const panelHeader = helpPanelDom.getElementsByClassName('panel-heading').item(0);
        expect(panelHeader).toExist();
        expect(panelHeader.innerHTML.indexOf("HELP") !== -1).toBe(true);
    });

    it('creates the component with custom props', () => {
        const helpPanel = ReactDOM.render(<HelpTextPanel
                        asPanel
                        id="fooid"
                        isVisible={true}
                        title="footitle"
                        helpText="foohelptext"
                        />, document.getElementById("container"));
        expect(helpPanel).toExist();

        const helpPanelDom = ReactDOM.findDOMNode(helpPanel);
        expect(helpPanelDom).toExist();
        expect(helpPanelDom.id).toBe("fooid");
        expect(helpPanelDom.className.indexOf('hidden') < 0).toBe(true);

        // header text
        const panelHeader = helpPanelDom.getElementsByClassName('panel-heading').item(0);
        expect(panelHeader).toExist();
        expect(panelHeader.innerHTML.indexOf("footitle") !== -1).toBe(true);

        // text in body
        const panelBody = helpPanelDom.getElementsByClassName('panel-body').item(0);
        expect(panelBody).toExist();
        expect(panelBody.innerHTML.indexOf("foohelptext") !== -1).toBe(true);
    });

});
