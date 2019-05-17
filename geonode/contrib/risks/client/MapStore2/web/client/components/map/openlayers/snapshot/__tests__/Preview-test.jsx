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
var GrabMap = require('../Preview');
var OLMap = require('../../../../map/openlayers/Map.jsx');


require('../../../../../utils/openlayers/Layers');
require('../../../../map/openlayers/plugins/OSMLayer');

describe("test the OL Snapshot Preview component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"><div id="map"></div><div id="snap"></div></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("snap"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('component creation', () => {
        const tb = ReactDOM.render(<GrabMap active={false}/>, document.getElementById("snap"));
        expect(tb).toExist();
    });
    it('component snapshot img creation', (done) => {
        const map = ReactDOM.render(<OLMap center={{y: 43.9, x: 10.3}} zoom={11} />, document.getElementById("map"));
        expect(map).toExist();
        let tb = ReactDOM.render(<GrabMap mapId="map" snapstate={{error: "Test"}} active={false} timeout={0} onSnapshotReady={() => { expect(tb.isTainted(false)); expect(tb.exportImage()).toExist(); done(); }}/>, document.getElementById("snap"));
        expect(tb).toExist();
        tb = ReactDOM.render(<GrabMap mapId="map" snapstate={{error: "Test"}} active={true} timeout={0} onSnapshotReady={() => { expect(tb.isTainted(false)); expect(tb.exportImage()).toExist(); done(); }}/>, document.getElementById("snap"));
    });
    it('component deactivation do not generate snapshot', () => {
        const map = ReactDOM.render(<OLMap center={{y: 43.9, x: 10.3}} zoom={11} />, document.getElementById("map"));
        expect(map).toExist();
        // set a big timeout to make you sure that the snapshot is not not generated
        let tb = ReactDOM.render(<GrabMap mapId="map" snapstate={{error: "Test"}} active={true} timeout={10000} onSnapshotReady={() => { expect(true).toBe(false); }}/>, document.getElementById("snap"));
        expect(tb).toExist();
        tb = ReactDOM.render(<GrabMap mapId="map" snapstate={{error: "Test"}} active={false} timeout={10000} onSnapshotReady={() => { expect(true).toBe(false); }}/>, document.getElementById("snap"));
    });
});
