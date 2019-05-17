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
var ScaleBar = require('../ScaleBar');
var expect = require('expect');

describe('leaflet ScaleBar component', () => {
    let map;

    beforeEach((done) => {
        document.body.innerHTML = '<div id="map"></div><div id="container"></div>';
        map = L.map("map");
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('create ScaleBar with defaults', () => {
        const sb = ReactDOM.render(<ScaleBar map={map}/>, document.getElementById("container"));
        expect(sb).toExist();
        const domMap = map.getContainer();
        const scaleBars = domMap.getElementsByClassName('leaflet-control-scale-line');
        expect(scaleBars.length).toBe(1);
    });
});
