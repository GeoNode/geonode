/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var MapList = require('../MapList.jsx');
var expect = require('expect');

describe('This test for MapList', () => {
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
        const mapList = ReactDOM.render(<MapList/>, document.getElementById("container"));
        expect(mapList).toExist();

        const dom = ReactDOM.findDOMNode(mapList);
        expect(dom).toExist();
        // check body existence
        const panelBody = dom.getElementsByClassName('panel-body');
        expect(panelBody.length).toBe(1);
        // check missing header
        const headings = dom.getElementsByClassName('panel-heading');
        expect(headings.length).toBe(0);
    });

    it('checks properties', () => {
        const testTitle = "testTitle";
        const mapList = ReactDOM.render(<MapList panelProps={{header: testTitle}}/>, document.getElementById("container"));
        expect(mapList).toExist();

        const dom = ReactDOM.findDOMNode(mapList);
        expect(dom).toExist();
        // check body
        const panelBody = dom.getElementsByClassName('panel-body');
        expect(panelBody.length).toBe(1, "Panel Body Missing");

        // check header
        const headings = dom.getElementsByClassName('panel-heading');
        expect(headings.length).toBe(1, "Panel Heading Missing");
        expect(headings[0].innerHTML).toBe(testTitle, "Panel Heading Incorrect");
    });

    it('checks data', () => {
        var map1 = {id: 1, name: "a", description: "description"};
        var map2 = {id: 2, name: "b", description: "description"};
        const mapList = ReactDOM.render(<MapList maps={[map1, map2]}/>, document.getElementById("container"));
        expect(mapList).toExist();
        const dom = ReactDOM.findDOMNode(mapList);
        expect(dom).toExist();

        // check body
        const panelBody = dom.getElementsByClassName('panel-body');
        expect(panelBody.length).toBe(1, "Panel Body Missing");

        // check list
        const list = panelBody[0].getElementsByClassName("list-group-item");
        expect(list.length).toBe(2, " list missing");
    });
});
