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
var ol = require('openlayers');
var MeasurementSupport = require('../MeasurementSupport');

describe('Openlayers MeasurementSupport', () => {
    var msNode;
    function getMapLayersNum(map) {
        return map.getLayers().getLength();
    }

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
        var viewOptions = {
            projection: 'EPSG:3857',
            center: [0, 0],
            zoom: 5
        };
        var map = new ol.Map({
          target: "map",
          view: new ol.View(viewOptions)
        });

        const cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                measurement={{
                    geomType: null
                }}
            />
        , msNode);

        expect(cmp).toExist();
    });

    it('test if a new layer is added to the map in order to allow drawing.', () => {
        var viewOptions = {
            projection: 'EPSG:3857',
            center: [0, 0],
            zoom: 5
        };
        var map = new ol.Map({
          target: "map",
          view: new ol.View(viewOptions)
        });

        let cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                measurement={{
                    geomType: null
                }}
            />
        , msNode);
        expect(cmp).toExist();

        let initialLayersNum = getMapLayersNum(map);
        cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                measurement={{
                    geomType: "LineString"
                }}
            />
        , msNode);
        expect(getMapLayersNum(map)).toBeGreaterThan(initialLayersNum);
    });

    it('test if drawing layers will be removed', () => {
        var viewOptions = {
            projection: 'EPSG:3857',
            center: [0, 0],
            zoom: 5
        };
        var map = new ol.Map({
          target: "map",
          view: new ol.View(viewOptions)
        });

        let cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                measurement={{
                    geomType: null
                }}
            />
        , msNode);
        expect(cmp).toExist();

        let initialLayersNum = getMapLayersNum(map);
        cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                measurement={{
                    geomType: "Polygon"
                }}
            />
        , msNode);
        expect(getMapLayersNum(map)).toBeGreaterThan(initialLayersNum);
        cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                measurement={{
                    geomType: null
                }}
            />
        , msNode);
        expect(getMapLayersNum(map)).toBe(initialLayersNum);
    });
});
