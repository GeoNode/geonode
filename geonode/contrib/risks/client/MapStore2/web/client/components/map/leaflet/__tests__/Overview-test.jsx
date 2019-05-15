/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var L = require('leaflet');
var Overview = require('../Overview');
var expect = require('expect');

describe('leaflet Overview component', () => {
    let map;

    beforeEach((done) => {
        document.body.innerHTML = '<div id="map"></div><div id="container"></div>';
        map = L.map("map", {
                center: [51.505, -0.09],
                zoom: 13
            });
        setTimeout(done);
    });

    afterEach((done) => {
        document.body.innerHTML = '<div id="map"></div><div id="container"></div>';
        map = L.map("map", {
                center: [51.505, -0.09],
                zoom: 13
            });
        setTimeout(done);
    });

    it('create Overview with defaults', () => {
        const ov = ReactDOM.render(<Overview map={map}/>, document.getElementById("container"));
        expect(ov).toExist();
        const domMap = map.getContainer();
        const overview = domMap.getElementsByClassName('leaflet-control-minimap');
        expect(overview.length).toBe(1);
    });
});
