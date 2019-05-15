/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var MapGrid = require('../MapGrid.jsx');
var expect = require('expect');

describe('This test for MapGrid', () => {
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
        const mapList = ReactDOM.render(<MapGrid/>, document.getElementById("container"));
        expect(mapList).toExist();

        const dom = ReactDOM.findDOMNode(mapList);
        expect(dom).toExist();
    });

    it('checks data', () => {
        var map1 = {id: 1, name: "a", description: "description"};
        var map2 = {id: 2, name: "b", description: "description"};
        let currentMap = {displayMetadataEdit: true};
        const mapList = ReactDOM.render(<MapGrid maps={[map1, map2]} currentMap={currentMap} show={true}/>, document.getElementById("container"));
        expect(mapList).toExist();
        const dom = ReactDOM.findDOMNode(mapList);
        expect(dom).toExist();

        // check list
        const list = dom.getElementsByClassName("map-thumb");
        expect(list.length).toBe(2, " list missing");
    });
});
