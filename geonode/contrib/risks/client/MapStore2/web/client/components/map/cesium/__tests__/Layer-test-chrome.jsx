/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var CesiumLayer = require('../Layer.jsx');
var expect = require('expect');
var Cesium = require('../../../../libs/cesium');

const assign = require('object-assign');

require('../../../../utils/cesium/Layers');
require('../plugins/OSMLayer');
require('../plugins/WMSLayer');
require('../plugins/BingLayer');
require('../plugins/GraticuleLayer');
require('../plugins/OverlayLayer');
require('../plugins/MarkerLayer');

window.CESIUM_BASE_URL = "web/client/libs/Cesium/Build/Cesium";

describe('Cesium layer', () => {
    let map;

    beforeEach((done) => {
        document.body.innerHTML = '<div id="map"></div><div id="container"></div><div id="container2"></div>';
        map = new Cesium.Viewer("map");
        map.imageryLayers.removeAll();
        setTimeout(done);
    });

    afterEach((done) => {
        /*eslint-disable */
        try {
            ReactDOM.unmountComponentAtNode(document.getElementById("map"));
            ReactDOM.unmountComponentAtNode(document.getElementById("container"));
            ReactDOM.unmountComponentAtNode(document.getElementById("container2"));
        } catch(e) {}
        /*eslint-enable */
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('missing layer', () => {
        var source = {
            "P_TYPE": "wrong ptype key"
        };
        // create layers
        var layer = ReactDOM.render(
            <CesiumLayer source={source}
                  map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        expect(map.imageryLayers.length).toBe(0);
    });

    it('creates a unknown source layer', () => {
        var options = {
            "name": "FAKE"
        };
        var source = {
            "ptype": "FAKE",
            "url": "http://demo.geo-solutions.it/geoserver/wms"
        };
        // create layers
        var layer = ReactDOM.render(
            <CesiumLayer source={source}
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        expect(map.imageryLayers.length).toBe(0);
    });

    it('creates source with missing ptype', () => {
        var options = {
            "name": "FAKE"
        };
        var source = {
            "P_TYPE": "wrong ptype key"
        };
        // create layers
        var layer = ReactDOM.render(
            <CesiumLayer source={source}
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        expect(map.imageryLayers.length).toBe(0);
    });

    it('creates a osm layer for cesium map', () => {
        var options = {};
        // create layers
        var layer = ReactDOM.render(
            <CesiumLayer type="osm"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        expect(map.imageryLayers.length).toBe(1);
    });

    it('creates a osm layer for cesium map', () => {
        var options = {
            "source": "osm",
            "title": "Open Street Map",
            "name": "mapnik",
            "group": "background"
        };
        // create layer
        var layer = ReactDOM.render(
            <CesiumLayer type="osm"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        expect(map.imageryLayers.length).toBe(1);
    });

    it('creates a wms layer for CesiumLayer map', () => {
        var options = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "url": "http://demo.geo-solutions.it/geoserver/wms"
        };
        // create layers
        var layer = ReactDOM.render(
            <CesiumLayer type="wms"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        expect(map.imageryLayers.length).toBe(1);
        expect(map.imageryLayers._layers[0]._imageryProvider._url).toBe('{s}');
        expect(map.imageryLayers._layers[0]._imageryProvider._tileProvider._subdomains.length).toBe(1);
    });

    it('creates a wms layer with single tile for CesiumLayer map', () => {
        var options = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "url": "http://demo.geo-solutions.it/geoserver/wms",
            "singleTile": true
        };
        // create layers
        var layer = ReactDOM.render(
            <CesiumLayer type="wms"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        expect(map.imageryLayers.length).toBe(1);
        expect(map.imageryLayers._layers[0]._imageryProvider._url.indexOf('http://demo.geo-solutions.it/geoserver/wms?service=WMS')).toBe(0);
    });

    it('creates a wms layer with multiple urls for CesiumLayer map', () => {
        var options = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "url": ["http://demo.geo-solutions.it/geoserver/wms", "http://demo.geo-solutions.it/geoserver/wms"]
        };
        // create layers
        var layer = ReactDOM.render(
            <CesiumLayer type="wms"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        expect(map.imageryLayers.length).toBe(1);
        expect(map.imageryLayers._layers[0]._imageryProvider._url).toBe('{s}');
        expect(map.imageryLayers._layers[0]._imageryProvider._tileProvider._subdomains.length).toBe(2);
    });

    it('creates a bing layer for leaflet map', () => {
        var options = {
            "type": "bing",
            "title": "Bing Aerial",
            "name": "Aerial",
            "group": "background"
        };
        // create layers
        var layer = ReactDOM.render(
            <CesiumLayer type="bing" options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        expect(map.imageryLayers.length).toBe(1);
    });

    it('switch osm layer visibility', () => {
        // create layers
        var layer = ReactDOM.render(
            <CesiumLayer type="osm"
                 options={{}} position={0} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        expect(map.imageryLayers.length).toBe(1);
        // not visibile layers are removed from the leaflet maps
        layer = ReactDOM.render(
            <CesiumLayer type="osm"
                 options={{visibility: false}} position={0} map={map}/>, document.getElementById("container"));
        expect(map.imageryLayers.length).toBe(0);
        layer = ReactDOM.render(
            <CesiumLayer type="osm"
                 options={{visibility: true}} position={0} map={map}/>, document.getElementById("container"));
        expect(map.imageryLayers.length).toBe(1);
    });

    it('changes wms layer opacity', () => {
        var options = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "opacity": 1.0,
            "url": "http://demo.geo-solutions.it/geoserver/wms"
        };
        // create layers
        var layer = ReactDOM.render(
            <CesiumLayer type="wms"
                 options={options} position={0} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        expect(map.imageryLayers.length).toBe(1);

        expect(layer.provider.alpha).toBe(1.0);
        layer = ReactDOM.render(
            <CesiumLayer type="wms"
                 options={assign({}, options, {opacity: 0.5})} position={0} map={map}/>, document.getElementById("container"));
        expect(layer.provider.alpha).toBe(0.5);
    });

    it('respects layer ordering 1', () => {
        var options1 = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample1",
            "group": "Meteo",
            "format": "image/png",
            "opacity": 1.0,
            "url": "http://demo.geo-solutions.it/geoserver/wms"
        };
        var options2 = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample2",
            "group": "Meteo",
            "format": "image/png",
            "opacity": 1.0,
            "url": "http://demo.geo-solutions.it/geoserver/wms"
        };
        // create layers
        let layer1 = ReactDOM.render(
            <CesiumLayer type="wms"
             options={options1} map={map} position={1}/>
                , document.getElementById("container"));

        expect(layer1).toExist();
        expect(map.imageryLayers.length).toBe(1);

        let layer2 = ReactDOM.render(
            <CesiumLayer type="wms"
             options={options2} map={map} position={2}/>
         , document.getElementById("container2"));

        expect(layer2).toExist();
        expect(map.imageryLayers.length).toBe(2);

        layer1 = ReactDOM.render(
            <CesiumLayer type="wms"
             options={options1} map={map} position={2}/>
                , document.getElementById("container"));

        layer2 = ReactDOM.render(
            <CesiumLayer type="wms"
             options={options2} map={map} position={1}/>
         , document.getElementById("container2"));

        expect(map.imageryLayers.get(0)).toBe(layer2.provider);
        expect(map.imageryLayers.get(1)).toBe(layer1.provider);
    });

    it('creates a graticule layer for cesium map', () => {
        var options = {
            "visibility": true
        };
        // create layers
        var layer = ReactDOM.render(
            <CesiumLayer type="graticule"
                 options={options} map={map}/>, document.getElementById("container"));


        expect(layer).toExist();
        expect(map.imageryLayers.length).toBe(1);
    });

    it('creates and overlay layer for cesium map', () => {
        let container = document.createElement('div');
        container.id = 'ovcontainer';
        document.body.appendChild(container);

        let element = document.createElement('div');
        element.id = 'overlay-1';
        document.body.appendChild(element);

        let options = {
            id: 'overlay-1',
            position: [13, 43]
        };
        // create layers
        let layer = ReactDOM.render(
            <CesiumLayer type="overlay"
                 options={options} map={map}/>, document.getElementById('ovcontainer'));

        expect(layer).toExist();
        expect(map.scene.primitives.length).toBe(1);
    });

    it('creates and overlay layer for cesium map with close support', () => {
        let container = document.createElement('div');
        container.id = 'ovcontainer';
        document.body.appendChild(container);

        let element = document.createElement('div');
        element.id = 'overlay-1';
        let closeElement = document.createElement('div');
        closeElement.className = 'close';
        element.appendChild(closeElement);
        document.body.appendChild(element);
        let closed = false;
        let options = {
            id: 'overlay-1',
            position: [13, 43],
            onClose: () => {
                closed = true;
            }
        };
        // create layers
        let layer = ReactDOM.render(
            <CesiumLayer type="overlay"
                 options={options} map={map}/>, document.getElementById('ovcontainer'));

        expect(layer).toExist();
        const content = map.scene.primitives.get(0)._content;
        expect(content).toExist();
        const close = content.getElementsByClassName('close')[0];
        close.click();
        expect(closed).toBe(true);
    });

    it('creates and overlay layer for cesium map with no data-reactid attributes', () => {
        let container = document.createElement('div');
        container.id = 'ovcontainer';
        document.body.appendChild(container);

        let element = document.createElement('div');
        element.id = 'overlay-1';
        let closeElement = document.createElement('div');
        closeElement.className = 'close';
        element.appendChild(closeElement);
        document.body.appendChild(element);
        let options = {
            id: 'overlay-1',
            position: [13, 43]
        };
        // create layers
        let layer = ReactDOM.render(
            <CesiumLayer type="overlay"
                 options={options} map={map}/>, document.getElementById('ovcontainer'));

        expect(layer).toExist();
        const content = map.scene.primitives.get(0)._content;
        expect(content).toExist();
        const close = content.getElementsByClassName('close')[0];
        expect(close.getAttribute('data-reactid')).toNotExist();
    });

    it('creates a marker layer for cesium map', () => {
        let options = {
            point: [13, 43]
        };
        // create layers
        let layer = ReactDOM.render(
            <CesiumLayer type="marker"
                 options={options} map={map}/>, document.getElementById('container'));
        expect(layer).toExist();
        expect(map.entities._entities.length).toBe(1);
    });

    it('respects layer ordering 2', () => {
        var options = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "opacity": 1.0,
            "url": "http://demo.geo-solutions.it/geoserver/wms"
        };
        // create layers
        var layer = ReactDOM.render(
            <CesiumLayer type="wms" position={10}
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();

        const position = map.imageryLayers.get(0)._position;
        expect(position).toBe(10);
    });
});
