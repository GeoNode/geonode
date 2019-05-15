/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var CesiumMap = require('../Map.jsx');
var CesiumLayer = require('../Layer.jsx');
var expect = require('expect');
var Cesium = require('../../../../libs/cesium');

require('../../../../utils/cesium/Layers');
require('../plugins/OSMLayer');

window.CESIUM_BASE_URL = "web/client/libs/Cesium/Build/Cesium";

describe('CesiumMap', () => {

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });
    afterEach((done) => {
        /*eslint-disable */
        try {
            ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        } catch(e) {}
        /*eslint-enable */
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates a div for cesium map with given id', () => {
        const map = ReactDOM.render(<CesiumMap id="mymap" center={{y: 43.9, x: 10.3}} zoom={11}/>, document.getElementById("container"));
        expect(map).toExist();
        expect(ReactDOM.findDOMNode(map).id).toBe('mymap');
    });

    it('creates a div for cesium map with default id (map)', () => {
        const map = ReactDOM.render(<CesiumMap center={{y: 43.9, x: 10.3}} zoom={11}/>, document.getElementById("container"));
        expect(map).toExist();
        expect(ReactDOM.findDOMNode(map).id).toBe('map');
    });

    it('creates multiple maps for different containers', () => {
        const container = ReactDOM.render(
        (
            <div>
                <div id="container1"><CesiumMap id="map1" center={{y: 43.9, x: 10.3}} zoom={11}/></div>
                <div id="container2"><CesiumMap id="map2" center={{y: 43.9, x: 10.3}} zoom={11}/></div>
            </div>
        ), document.getElementById("container"));
        expect(container).toExist();

        expect(document.getElementById('map1')).toExist();
        expect(document.getElementById('map2')).toExist();
    });

    it('populates the container with cesium objects', () => {
        const map = ReactDOM.render(<CesiumMap center={{y: 43.9, x: 10.3}} zoom={11}/>, document.getElementById("container"));
        expect(map).toExist();
        expect(document.getElementsByClassName('cesium-viewer').length).toBe(1);
        expect(document.getElementsByClassName('cesium-viewer-cesiumWidgetContainer').length).toBe(1);
        expect(document.getElementsByClassName('cesium-widget').length).toBe(1);
    });

    it('check layers init', () => {
        var options = {
            "visibility": true
        };
        const map = ReactDOM.render(<CesiumMap center={{y: 43.9, x: 10.3}} zoom={11}>
            <CesiumLayer type="osm" options={options} />
        </CesiumMap>, document.getElementById("container"));
        expect(map).toExist();
        expect(map.map.imageryLayers.length).toBe(1);
    });

    it('check if the handler for "moveend" event is called', () => {
        const expectedCalls = 2;
        const testHandlers = {
            handler: () => {}
        };
        var spy = expect.spyOn(testHandlers, 'handler');

        const map = ReactDOM.render(
            <CesiumMap
                center={{y: 43.9, x: 10.3}}
                zoom={11}
                onMapViewChanges={testHandlers.handler}
            />
        , document.getElementById("container"));

        const cesiumMap = map.map;
        cesiumMap.camera.moveEnd.addEventListener(() => {
            expect(spy.calls.length).toEqual(expectedCalls);
            expect(spy.calls[0].arguments.length).toEqual(6);

            expect(spy.calls[0].arguments[0].y).toEqual(43.9);
            expect(spy.calls[0].arguments[0].x).toEqual(10.3);
            expect(spy.calls[0].arguments[1]).toEqual(11);

            expect(spy.calls[1].arguments[0].y).toEqual(44);
            expect(spy.calls[1].arguments[0].x).toEqual(10);
            expect(spy.calls[1].arguments[1]).toEqual(12);

            for (let c = 0; c < expectedCalls; c++) {
                expect(spy.calls[c].arguments[2].bounds).toExist();
                expect(spy.calls[c].arguments[2].crs).toExist();
                expect(spy.calls[c].arguments[3].height).toExist();
                expect(spy.calls[c].arguments[3].width).toExist();
            }
        });
        cesiumMap.camera.setView({
            destination: Cesium.Cartesian3.fromDegrees(
                10,
                44,
                5000000
            )
        });
    });

    it('check if the map changes when receive new props', () => {
        let map = ReactDOM.render(
            <CesiumMap
                center={{y: 43.9, x: 10.3}}
                zoom={10}
            />
        , document.getElementById("container"));

        const cesiumMap = map.map;

        map = ReactDOM.render(
            <CesiumMap
                center={{y: 44, x: 10}}
                zoom={12}
            />
        , document.getElementById("container"));

        expect(Math.round(cesiumMap.camera.positionCartographic.height - map.getHeightFromZoom(12))).toBe(0);
        expect(Math.round(cesiumMap.camera.positionCartographic.latitude * 180.0 / Math.PI)).toBe(44);
        expect(Math.round(cesiumMap.camera.positionCartographic.longitude * 180.0 / Math.PI)).toBe(10);
    });

    it('check that the map orientation does not change on pan / zoom', () => {
        let map = ReactDOM.render(
            <CesiumMap
                center={{y: 43.9, x: 10.3}}
                zoom={10}
            />
        , document.getElementById("container"));

        const cesiumMap = map.map;
        cesiumMap.camera.lookUp(1.0);
        cesiumMap.camera.lookRight(1.0);
        const precision = Math.pow(10, 8);
        const heading = Math.round(cesiumMap.camera.heading * precision) / precision;
        const pitch = Math.round(cesiumMap.camera.pitch * precision) / precision;
        const roll = Math.round(cesiumMap.camera.roll * precision) / precision;

        map = ReactDOM.render(
            <CesiumMap
                center={{y: 44, x: 10}}
                zoom={12}
            />
        , document.getElementById("container"));

        expect(Math.round(cesiumMap.camera.heading * precision) / precision).toBe(heading);
        expect(Math.round(cesiumMap.camera.pitch * precision) / precision).toBe(pitch);
        expect(Math.round(cesiumMap.camera.roll * precision) / precision).toBe(roll);

    });
});
