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
var GrabMap = require('../GrabMap');

describe("the OL GrabMap component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="snap"></div><div id="map"><canvas></canvas></div>';
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
    /*it('component update', () => {
        let tb = ReactDOM.render(<GrabMap active={false}/>, document.getElementById("snap"));
        expect(tb).toExist();
        tb = ReactDOM.render(<GrabMap active={false}/>, document.getElementById("snap"));
    });*/
    it('component snapshot img creation', (done) => {
        let layers = [{
            "source": "mapquest",
            "title": "MapQuest OpenStreetMap",
            "name": "osm",
            "group": "background"
        }, {
            "type": "vector",
            "features": [{
                id: "1",
                type: "Feature",
                geometry: {
                    type: 'Point',
                    coordinates: [0, 0]
                }
            }]
        }];
        let map = {projection: "EPSG:900913", units: "m", center: { x: 11.25, y: 43.40, crs: "EPSG:4326"},
                    zoom: 5, maxExtent: [-20037508.34, -20037508.34, 20037508.34, 20037508.34],
                    bbox: {bounds: {minx: -18.6328125, miny: 31.728167146023935, maxx: 41.1328125, maxy: 53.199451902831555 },
                     crs: "EPSG:4326", rotation: 0}, size: {height: 512, width: 512}, mapStateSource: "map"};
        let tb = ReactDOM.render(<GrabMap config={map} layers={layers} snapstate={{state: "DISABLED"}} active={false} timeout={0} onSnapshotReady={() => { done(); }}/>, document.getElementById("snap"));
        expect(tb).toExist();
        tb = ReactDOM.render(<GrabMap config={map} layers={layers} snapstate={{state: "DISABLED"}} active={true} timeout={0} onSnapshotReady={() => { done(); }}/>, document.getElementById("snap"));
        // emulate map load
        tb.layerLoading();
        tb.layerLoad();
        // force snapshot creation
        tb.createSnapshot();
    });

});
