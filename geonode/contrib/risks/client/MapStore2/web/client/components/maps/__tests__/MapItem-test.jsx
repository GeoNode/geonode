/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var MapItem = require('../MapItem.jsx');
var expect = require('expect');

const TestUtils = require('react-addons-test-utils');

describe('This test for MapItem', () => {
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
        const mapItem = ReactDOM.render(<MapItem map={{}}/>, document.getElementById("container"));
        expect(mapItem).toExist();

        const mapItemDom = ReactDOM.findDOMNode(mapItem);
        expect(mapItemDom).toExist();

        expect(mapItemDom.className).toBe('list-group-item');
        const headings = mapItemDom.getElementsByClassName('list-group-item-heading');
        expect(headings.length).toBe(0);
    });
    // test DEFAULTS
    it('creates the component with data', () => {
        const testName = "test";
        const testDescription = "testDescription";
        const mapItem = ReactDOM.render(<MapItem map={{name: testName, description: testDescription}}/>, document.getElementById("container"));
        expect(mapItem).toExist();

        const mapItemDom = ReactDOM.findDOMNode(mapItem);
        expect(mapItemDom).toExist();

        expect(mapItemDom.className).toBe('list-group-item');
        const headings = mapItemDom.getElementsByClassName('list-group-item-heading');
        expect(headings.length).toBe(1);
        expect(headings[0].innerHTML).toBe(testName);
    });

    it('test viewer url', () => {
        const testName = "test";
        const testDescription = "testDescription";
        var component = TestUtils.renderIntoDocument(<MapItem id={1} map={{id: 1, name: testName, description: testDescription}} mapType="leaflet" viewerUrl="viewer"/>);
        var a = TestUtils.findRenderedDOMComponentWithTag(
           component, 'a'
        );
        expect(a.href).toContain("viewer?type=leaflet&mapId=1");
    });
});
