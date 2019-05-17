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
var Legend = require('../Legend');

const TestUtils = require('react-addons-test-utils');

describe("test the Layer legend", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('test component creation', () => {
        let layer = {
            "type": "osm",
            "title": "Open Street Map",
            "name": "mapnik",
            "group": "background",
            "visibility": true
        };
        const tb = ReactDOM.render(<Legend layer={layer}/>, document.getElementById("container"));
        expect(tb).toExist();

    });

    it('create component without layer', () => {

        const tb = ReactDOM.render(<Legend />, document.getElementById("container"));
        expect(tb).toExist();

    });

    it('test legend content', () => {
        let layer = {
            "type": "wms",
            "url": "http://test2/reflector/open/service",
            "visibility": true,
            "title": "test layer 3 (no group)",
            "name": "layer3",
            "format": "image/png"
        };
        var tb = ReactDOM.render(<Legend layer={layer} />, document.getElementById("container"));
        let thumbs = TestUtils.scryRenderedDOMComponentsWithTag(tb, "img");
        expect(thumbs.length).toBe(1);
    });

});
