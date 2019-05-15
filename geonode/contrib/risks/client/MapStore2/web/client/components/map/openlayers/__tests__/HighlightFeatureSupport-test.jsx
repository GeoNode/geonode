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
let ol = require('openlayers');
const HighlightFeatureSupport = require('../HighlightFeatureSupport');

let createVectorLayer = function(options) {
    let features;
    if (options.features) {
        let featureCollection = options.features;
        if (Array.isArray(options.features)) {
            featureCollection = { "type": "FeatureCollection", features: featureCollection};
        }
        features = (new ol.format.GeoJSON()).readFeatures(featureCollection);
        features.forEach((f) => f.getGeometry().transform('EPSG:4326', options.crs || 'EPSG:3857'));
    }
    const source = new ol.source.Vector({
        features: features
    });

    return new ol.layer.Vector({
        msId: options.id,
        source: source,
        zIndex: options.zIndex
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

describe('HighlightFeatureSupport Ol', () => {
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


    it('create a OL HighlightFeatureSupport component', () => {
        var viewOptions = {
            projection: 'EPSG:3857',
            center: [0, 0],
            zoom: 5
        };
        var map = new ol.Map({
          target: "map",
          view: new ol.View(viewOptions)
        });
        let vector = createVectorLayer(layer);
        map.addLayer(vector);
        let cmp = ReactDOM.render(<HighlightFeatureSupport map={map}/>, msNode);
        expect(cmp).toExist();
        cmp = ReactDOM.render(<HighlightFeatureSupport map={map} status="enabled"/>, msNode);
        cmp.selectionChange();
        cmp = ReactDOM.render(<HighlightFeatureSupport map={map} status="disabled"/>, msNode);
    });
});
