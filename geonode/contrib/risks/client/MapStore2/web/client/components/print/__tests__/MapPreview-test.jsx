/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var React = require('react');
var ReactDOM = require('react-dom');
var MapPreview = require('../MapPreview');

describe("Test the MapPreview component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates component with defaults', () => {
        const cmp = ReactDOM.render(<MapPreview/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
    });

    it('creates a leaflet map', () => {
        const cmp = ReactDOM.render(<MapPreview map={{center: {x: 10.0, y: 40.0}, zoom: 5}}/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.getElementsByClassName('leaflet-map-pane').length).toBe(1);
    });

    it('creates a openlayers map', () => {
        const cmp = ReactDOM.render(<MapPreview mapType="openlayers" map={{center: {x: 10.0, y: 40.0}, zoom: 5}}/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.getElementsByClassName('ol-viewport').length).toBe(1);
    });

    it('creates a scalebox', () => {
        const cmp = ReactDOM.render(<MapPreview map={{center: {x: 10.0, y: 40.0}, zoom: 5, scaleZoom: 1}} scales={[10, 20, 30]} />, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.getElementsByTagName('select').length).toBe(1);
        expect(node.getElementsByTagName('select')[0].selectedIndex).toBe(1);
    });

    it('creates a map with layers', () => {
        const layers = [{
            name: 'layer1',
            type: "wms",
            visibility: false,
            url: "http://fake"
        }, {
            name: 'layer2',
            visibility: true,
            type: "osm"
        }, {
            name: 'layer3',
            visibility: true,
            type: "wms",
            url: "http://fake"
        }];
        const cmp = ReactDOM.render(<MapPreview layers={layers} map={{center: {x: 10.0, y: 40.0}, zoom: 5}}/>, document.getElementById("container"));
        expect(cmp).toExist();

        const node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        expect(node.getElementsByClassName('leaflet-layer').length).toBe(2);
    });
});
