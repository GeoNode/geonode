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
var MeasurementSupport = require('../MeasurementSupport');

describe('Leaflet MeasurementSupport', () => {
    var msNode;
    function getMapLayersNum(map) {
        return Object.keys(map._layers).length;
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
        let map = L.map("map");
        let proj = "EPSG:3857";
        let measurement = {
            geomType: null
        };

        const cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                projection={proj}
                measurement={measurement}
                changeMeasurementState={() => {}}
            />
        , msNode);
        expect(cmp).toExist();
    });

    it('test rendering', () => {
        let myMessages = {message: "message"};
        let drawLocal = L.drawLocal;
        L.drawLocal = null;
        const cmp = ReactDOM.render(
            <MeasurementSupport
                messages={myMessages}
            />
        , msNode);
        expect(cmp).toExist();
        expect(L.drawLocal).toEqual(myMessages);
        // restoring old value of drawLocal because other test would fail otherwise.
        // L is global so drawLocal need to be restore to default value
        L.drawLocal = drawLocal;
    });

    it('test if a new layer is added to the map in order to allow drawing.', () => {
        let map = L.map("map", {
            center: [51.505, -0.09],
            zoom: 13
        });
        let proj = "EPSG:3857";
        let measurement = {
            geomType: null
        };
        let initialLayersNum = getMapLayersNum(map);
        let cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                projection={proj}
                measurement={measurement}
                changeMeasurementState={() => {}}
            />
        , msNode);
        expect(cmp).toExist();

        cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                projection={proj}
                measurement={{geomType: "LineString"}}
                changeMeasurementState={() => {}}
            />
        , msNode);
        expect(getMapLayersNum(map)).toBeGreaterThan(initialLayersNum);
    });

    it('test if drawing layers will be removed', () => {
        let map = L.map("map", {
            center: [51.505, -0.09],
            zoom: 13
        });
        let proj = "EPSG:3857";
        let measurement = {
            geomType: null
        };
        let cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                projection={proj}
                measurement={measurement}
                changeMeasurementState={() => {}}
            />
        , msNode);
        expect(cmp).toExist();

        let initialLayersNum = getMapLayersNum(map);
        cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                projection={proj}
                measurement={{
                    geomType: "Polygon"
                }}
                changeMeasurementState={() => {}}
            />
        , msNode);
        expect(getMapLayersNum(map)).toBeGreaterThan(initialLayersNum);
        cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                projection={proj}
                measurement={{
                    geomType: null
                }}
                changeMeasurementState={() => {}}
            />
        , msNode);
        expect(getMapLayersNum(map)).toBe(initialLayersNum);
    });

    it('test map onClick handler for POINT tool', () => {
        let newMeasureState;
        let map = L.map("map", {
            center: [51.505, -0.09],
            zoom: 13
        });
        let proj = "EPSG:3857";
        let measurement = {
            geomType: null
        };
        let cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                projection={proj}
                measurement={measurement}
                changeMeasurementState={(data) => {newMeasureState = data; }}
            />
        , msNode);
        expect(cmp).toExist();

        cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                projection={proj}
                measurement={{
                    geomType: "Point"
                }}
                changeMeasurementState={(data) => {newMeasureState = data; }}
            />
        , msNode);
        expect(cmp).toExist();

        document.getElementById('map').addEventListener('click', () => {
            expect(newMeasureState).toExist();
        });
        document.getElementById('map').click();
    });

    it('test map onClick handler for LINE tool', () => {
        let newMeasureState;
        let map = L.map("map", {
            center: [51.505, -0.09],
            zoom: 13
        });
        let proj = "EPSG:3857";
        let measurement = {
            geomType: null
        };
        let cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                projection={proj}
                measurement={measurement}
                changeMeasurementState={(data) => {newMeasureState = data; }}
            />
        , msNode);
        expect(cmp).toExist();

        cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                projection={proj}
                measurement={{
                    geomType: "LineString"
                }}
                changeMeasurementState={(data) => {newMeasureState = data; }}
            />
        , msNode);

        document.getElementById('map').addEventListener('click', () => {
            expect(newMeasureState).toExist();
        });
        document.getElementById('map').click();
    });

    it('test map onClick handler for AREA tool', () => {
        let newMeasureState;
        let map = L.map("map", {
            center: [51.505, -0.09],
            zoom: 13
        });
        let proj = "EPSG:3857";
        let measurement = {
            geomType: null
        };
        let cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                projection={proj}
                measurement={measurement}
                changeMeasurementState={(data) => {newMeasureState = data; }}
            />
        , msNode);
        expect(cmp).toExist();

        cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                projection={proj}
                measurement={{
                    geomType: "Polygon"
                }}
                changeMeasurementState={(data) => {newMeasureState = data; }}
            />
        , msNode);
        document.getElementById('map').addEventListener('click', () => {
            expect(newMeasureState).toExist();
        });
        document.getElementById('map').click();
    });

    it('test map onClick handler for BEARING tool', () => {
        let newMeasureState;
        let map = L.map("map", {
            center: [51.505, -0.09],
            zoom: 13
        });
        let proj = "EPSG:3857";
        let measurement = {
            geomType: null
        };
        let cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                projection={proj}
                measurement={measurement}
                changeMeasurementState={(data) => {newMeasureState = data; }}
            />
        , msNode);
        expect(cmp).toExist();

        cmp = ReactDOM.render(
            <MeasurementSupport
                map={map}
                projection={proj}
                measurement={{
                    geomType: "Bearing"
                }}
                changeMeasurementState={(data) => {newMeasureState = data; }}
            />
        , msNode);
        document.getElementById('map').addEventListener('click', () => {
            expect(newMeasureState).toExist();
        });
        document.getElementById('map').click();
    });

});
