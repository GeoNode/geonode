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
var L = require('leaflet');
var DrawSupport = require('../DrawSupport');

describe('Leaflet DrawSupport', () => {
    var msNode;

    beforeEach((done) => {
        document.body.innerHTML = '<div id="map" style="heigth: 100px; width: 100px"></div><div id="ms"></div>';
        msNode = document.getElementById('ms');
        setTimeout(done);
    });
    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(msNode);
        document.body.innerHTML = '';
        msNode = undefined;
        setTimeout(done);
    });

    it('test creation', () => {
        let map = L.map("map", {
            center: [51.505, -0.09],
            zoom: 13
        });
        const cmp = ReactDOM.render(
            <DrawSupport
                map={map}
                drawOwner="me"
            />
        , msNode);
        expect(cmp).toExist();
    });

    it('test circle drawing creation.', () => {
        let map = L.map("map", {
            center: [51.505, -0.09],
            zoom: 13
        });

        let cmp = ReactDOM.render(
            <DrawSupport
                map={map}
                drawOwner="me"
            />
        , msNode);
        expect(cmp).toExist();

        cmp = ReactDOM.render(
            <DrawSupport
                map={map}
                drawStatus="start"
                drawMethod="Circle"
                drawOwner="me"
            />
        , msNode);

        expect(map._layers).toExist();
    });

    it('test if drawing layers will be removed', () => {
        let map = L.map("map", {
            center: [51.505, -0.09],
            zoom: 13
        });
        let cmp = ReactDOM.render(
            <DrawSupport
                map={map}
                drawOwner="me"
                drawStatus="create"
                drawMethod="BBOX"
            />
        , msNode);
        expect(cmp).toExist();

        cmp = ReactDOM.render(
            <DrawSupport
                map={map}
                drawOwner="me"
                drawStatus="clean"
                drawMethod="BBOX"
            />
        , msNode);
        expect(Object.keys(map._layers).length).toBe(0);
    });

    it('test map onClick handler created circle', () => {
        let bounds = L.latLngBounds(L.latLng(40.712, -74.227), L.latLng(40.774, -74.125));
        let layer = {
                    getBounds: function() { return bounds; },
                    toGeoJSON: function() {return {geometry: {coordinates: [0, 0]}}; }
                };
        let map = L.map("map", {
            center: [51.505, -0.09],
            zoom: 13
        });
        const cmp = ReactDOM.render(
            <DrawSupport
                map={map}
                drawOwner="me"
                drawStatus="start"
                drawMethod="Circle"
            />
        , msNode);
        expect(cmp).toExist();
        cmp.drawLayer = {addData: function() {return true; }};
        cmp.onDraw.created.call(cmp, {layer: layer, layerType: "circle"});
    });
    it('test draw replace', () => {
        let map = L.map("map", {
            center: [51.505, -0.09],
            zoom: 13
        });
        let cmp = ReactDOM.render(
            <DrawSupport
                map={map}
                drawOwner="me"
                drawStatus="start"
                drawMethod="Circle"
            />
        , msNode);
        expect(cmp).toExist();
        cmp = ReactDOM.render(
            <DrawSupport
                map={map}
                drawOwner="me"
                drawStatus="replace"
                drawMethod="Circle"
                features={[{
                    projection: "EPSG:4326",
                    coordinates: [ -21150.703250721977, 5855989.620460],
                    radius: 122631.43,
                    type: "Polygon"}
                ]}
            />
        , msNode);
    });

});
