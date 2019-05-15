/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const React = require('react');
const ReactDOM = require('react-dom');
let L = require('leaflet');
const HighlightFeatureSupport = require('../HighlightFeatureSupport');

let defaultStyle = {
    radius: 5,
    color: "red",
    weight: 1,
    opacity: 1,
    fillOpacity: 0
};

let createVectorLayer = function(options) {
    const {hideLoading} = options;
    return L.geoJson([]/* options.features */, {
        pointToLayer: options.styleName !== "marker" ? function(feature, latlng) {
            return L.circleMarker(latlng, options.style || defaultStyle);
        } : null,
        hideLoading: hideLoading,
        style: options.style || defaultStyle
    });
};
const layer = {
        "type": "vector",
        "name": "Selected items",
        "id": "featureselector",
        "features": [],
        "crs": "EPSG:4326",
        "hideLoading": true,
        "visibility": true,
        "style": {
            "radius": 10,
            "weight": 3,
            "opacity": 1,
            "fillOpacity": 0.5,
            "color": "blue",
            "fillColor": "blue"
        }
};

describe('HighlightFeatureSupport', () => {
    let msNode;
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

    it('create a HighlightFeatureSupport component', () => {
        let map = L.map("map", {
            center: [51.505, -0.09],
            zoom: 13
        });
        let vector = createVectorLayer(layer);
        vector.addTo(map);
        const cmp = ReactDOM.render(<HighlightFeatureSupport map={map}/>, msNode);
        expect(cmp).toExist();
    });
    it('create a HighlightFeatureSupport component enabled and test click', () => {
        let map = L.map("map", {
            center: [51.505, -0.09],
            zoom: 13
        });
        let vector = createVectorLayer(layer);
        vector.addTo(map);
        const cmp = ReactDOM.render(<HighlightFeatureSupport map={map} status="enabled"/>, msNode);
        expect(cmp).toExist();
        cmp.featureClicked({layer: vector, originalEvent: {shiftKey: false}});
        cmp.featureClicked({layer: vector, originalEvent: {shiftKey: true}});
        // cmp.setProps({status: "disabled"});
    });
});
