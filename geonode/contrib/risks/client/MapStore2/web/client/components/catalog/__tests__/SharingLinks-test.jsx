 /**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactDOM = require('react-dom');
const SharingLinks = require('../SharingLinks.jsx');
const expect = require('expect');

describe('Tests for SharingLinks', () => {

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
        const component = ReactDOM.render(<SharingLinks/>, document.getElementById('container'));
        expect(component).toExist();
        // no dom node should be rendered with the default values
        const componentDom = ReactDOM.findDOMNode(component);
        expect(componentDom).toNotExist();
    });

    it('create the component with some links', () => {
        const links = [{'url': 'url1'}, {'url': 'url2'}];
        const component = ReactDOM.render(<SharingLinks links={links}/>, document.getElementById('container'));
        expect(component).toExist();
        // no dom node should be rendered with the default values
        const componentDom = ReactDOM.findDOMNode(component);
        expect(componentDom).toExist();
        // let's click on the share button
        const shareButtons = document.getElementsByTagName('button');
        expect(shareButtons.length).toBe(1);
        shareButtons[0].click();
        // we should have two buttons now
        const buttons = document.getElementById('links-popover').getElementsByTagName('button');
        expect(buttons.length).toBe(2);
        // we should have two inputs now
        const inputs = document.getElementById('links-popover').getElementsByTagName('input');
        expect(inputs.length).toBe(2);
        // check that the inputs contain the correct url values
        let values = [];
        values.push(inputs[0].value);
        values.push(inputs[1].value);
        expect(values).toInclude('url1');
        expect(values).toInclude('url2');
    });
});
