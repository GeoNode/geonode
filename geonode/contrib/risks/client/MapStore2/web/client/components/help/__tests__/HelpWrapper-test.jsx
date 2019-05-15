/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var HelpWrapper = require('../HelpWrapper');
var expect = require('expect');

describe('Test for HelpWrapper', () => {
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
    it('wraps child component properly', () => {
        const helpWrapper = ReactDOM.render(<HelpWrapper><div id="child-div" key="child-key"></div></HelpWrapper>, document.getElementById("container"));
        expect(helpWrapper).toExist();

        const helpWrapperDom = ReactDOM.findDOMNode(helpWrapper);
        expect(helpWrapperDom).toExist();

        // creates a help badge
        const badge = helpWrapperDom.getElementsByTagName('span').item(0);
        expect(badge).toExist();
        expect(badge.id).toExist();
        expect(badge.id).toBe("helpbadge-child-key");
        expect(badge.className.indexOf('badge') >= 0).toBe(true);
        expect(badge.className.indexOf('hidden') >= 0).toBe(true);
        expect(badge.innerHTML).toBe("?");

        // the wrapped child from outside
        const child = helpWrapperDom.getElementsByTagName('div').item(0);
        expect(child).toExist();
        expect(child.id).toExist();
        expect(child.id).toBe("child-div");
    });

});
