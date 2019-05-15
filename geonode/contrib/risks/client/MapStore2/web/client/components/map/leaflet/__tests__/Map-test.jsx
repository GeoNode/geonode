/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var LeafletMap = require('../Map.jsx');
var LeafLetLayer = require('../Layer.jsx');
var expect = require('expect');
var mapUtils = require('../../../../utils/MapUtils');

require('../../../../utils/leaflet/Layers');
require('../plugins/OSMLayer');

describe('LeafletMap', () => {

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });
    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates a div for leaflet map with given id', () => {
        const map = ReactDOM.render(<LeafletMap id="mymap" center={{y: 43.9, x: 10.3}} zoom={11}/>, document.getElementById("container"));
        expect(map).toExist();
        expect(ReactDOM.findDOMNode(map).id).toBe('mymap');
    });

    it('creates a div for leaflet map with default id (map)', () => {
        const map = ReactDOM.render(<LeafletMap center={{y: 43.9, x: 10.3}} zoom={11}/>, document.getElementById("container"));
        expect(map).toExist();
        expect(ReactDOM.findDOMNode(map).id).toBe('map');
    });

    it('creates multiple maps for different containers', () => {
        const container = ReactDOM.render(
        (
            <div>
                <div id="container1"><LeafletMap id="map1" center={{y: 43.9, x: 10.3}} zoom={11}/></div>
                <div id="container2"><LeafletMap id="map2" center={{y: 43.9, x: 10.3}} zoom={11}/></div>
            </div>
        ), document.getElementById("container"));
        expect(container).toExist();

        expect(document.getElementById('map1')).toExist();
        expect(document.getElementById('map2')).toExist();
    });

    it('populates the container with leaflet objects', () => {
        const map = ReactDOM.render(<LeafletMap center={{y: 43.9, x: 10.3}} zoom={11}/>, document.getElementById("container"));
        expect(map).toExist();
        expect(document.getElementsByClassName('leaflet-map-pane').length).toBe(1);
        expect(document.getElementsByClassName('leaflet-tile-pane').length).toBe(1);
        expect(document.getElementsByClassName('leaflet-objects-pane').length).toBe(1);
        expect(document.getElementsByClassName('leaflet-control-container').length).toBe(1);
    });

    it('enables leaflet controls', () => {
        const map = ReactDOM.render(<LeafletMap center={{y: 43.9, x: 10.3}} zoom={11}/>, document.getElementById("container"));
        expect(map).toExist();
        expect(document.getElementsByClassName('leaflet-control-zoom-in').length).toBe(1);

        const leafletMap = map.map;
        expect(leafletMap).toExist();

        const zoomIn = document.getElementsByClassName('leaflet-control-zoom-in')[0];
        zoomIn.click();
        expect(leafletMap.getZoom()).toBe(12);

        const zoomOut = document.getElementsByClassName('leaflet-control-zoom-out')[0];
        zoomOut.click();
        expect(leafletMap.getZoom()).toBe(11);
    });

    it('check layers init', () => {
        var options = {
            "visibility": true
        };
        const map = ReactDOM.render(<LeafletMap center={{y: 43.9, x: 10.3}} zoom={11}>
            <LeafLetLayer type="osm" options={options} />
        </LeafletMap>, document.getElementById("container"));
        expect(map).toExist();
        expect(document.getElementsByClassName('leaflet-layer').length).toBe(1);
    });

    it('check if the handler for "moveend" event is called', () => {
        const expectedCalls = 2;
        const testHandlers = {
            handler: () => {}
        };
        var spy = expect.spyOn(testHandlers, 'handler');

        const map = ReactDOM.render(
            <LeafletMap
                center={{y: 43.9, x: 10.3}}
                zoom={11}
                onMapViewChanges={testHandlers.handler}
            />
        , document.getElementById("container"));

        const leafletMap = map.map;

        leafletMap.on('moveend', () => {
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
        leafletMap.setView({lat: 44, lng: 10}, 12);
    });

    it('check if the handler for "click" event is called', (done) => {
        const testHandlers = {
            handler: () => {}
        };
        var spy = expect.spyOn(testHandlers, 'handler');

        const map = ReactDOM.render(
            <LeafletMap
                center={{y: 43.9, x: 10.3}}
                zoom={11}
                onClick={testHandlers.handler}
            />
        , document.getElementById("container"));

        const leafletMap = map.map;
        const mapDiv = leafletMap.getContainer();

        mapDiv.click();
        setTimeout(() => {
            expect(spy.calls.length).toEqual(1);
            expect(spy.calls[0].arguments.length).toEqual(1);
            expect(spy.calls[0].arguments[0].pixel).toExist();
            expect(spy.calls[0].arguments[0].latlng).toExist();
            expect(spy.calls[0].arguments[0].modifiers).toExist();
            expect(spy.calls[0].arguments[0].modifiers.alt).toEqual(false);
            expect(spy.calls[0].arguments[0].modifiers.ctrl).toEqual(false);
            expect(spy.calls[0].arguments[0].modifiers.shift).toEqual(false);
            done();
        }, 600);
    });

    it('check if the map changes when receive new props', () => {
        let map = ReactDOM.render(
            <LeafletMap
                center={{y: 43.9, x: 10.3}}
                zoom={11.6}
                measurement={{}}
            />
        , document.getElementById("container"));

        const leafletMap = map.map;
        expect(leafletMap.getZoom()).toBe(12);
        map = ReactDOM.render(
            <LeafletMap
                center={{y: 44, x: 10}}
                zoom={10.4}
                measurement={{}}
            />
        , document.getElementById("container"));
        expect(leafletMap.getZoom()).toBe(10);
        expect(leafletMap.getCenter().lat).toBe(44);
        expect(leafletMap.getCenter().lng).toBe(10);
    });

    it('check if the map has "auto" cursor as default', () => {
        const map = ReactDOM.render(
            <LeafletMap
                center={{y: 43.9, x: 10.3}}
                zoom={11}
            />
        , document.getElementById("container"));

        const leafletMap = map.map;
        const mapDiv = leafletMap.getContainer();
        expect(mapDiv.style.cursor).toBe("auto");
    });

    it('check if the map can be created with a custom cursor', () => {
        const map = ReactDOM.render(
            <LeafletMap
                center={{y: 43.9, x: 10.3}}
                zoom={11}
                mousePointer="pointer"
            />
        , document.getElementById("container"));

        const leafletMap = map.map;
        const mapDiv = leafletMap.getContainer();
        expect(mapDiv.style.cursor).toBe("pointer");
    });

    it('test COMPUTE_BBOX_HOOK hook execution', () => {
        // instanciating the map that will be used to compute the bounfing box
        let map = ReactDOM.render(<LeafletMap id="mymap" center={{y: 43.9, x: 10.3}} zoom={11}/>, document.getElementById("container"));
        // computing the bounding box for the new center and the new zoom
        const bbox = mapUtils.getBbox({y: 44, x: 10}, 5);
        // update the map with the new center and the new zoom so we can check our computed bouding box
        map = ReactDOM.render(<LeafletMap id="mymap" center={{y: 44, x: 10}} zoom={5}/>, document.getElementById("container"));
        const mapBbox = map.map.getBounds().toBBoxString().split(',');
        // check our computed bounding box agains the map computed one
        expect(bbox).toExist();
        expect(mapBbox).toExist();
        expect(bbox.bounds).toExist();
        expect(bbox.bounds.minx).toBe(mapBbox[0]);
        expect(bbox.bounds.miny).toBe(mapBbox[1]);
        expect(bbox.bounds.maxx).toBe(mapBbox[2]);
        expect(bbox.bounds.maxy).toBe(mapBbox[3]);
        expect(bbox.crs).toExist();
        // in the case of leaflet the bounding box CRS should always be "EPSG:4326" and the roation 0
        expect(bbox.crs).toBe("EPSG:4326");
        expect(bbox.rotation).toBe(0);
    });

    it('check that new props, current props and map state values are used', () => {

        // instanciate the leaflet map
        let map = ReactDOM.render(<LeafletMap id="mymap" center={{y: 40.0, x: 10.0}} zoom={10}/>,
                        document.getElementById("container"));

        // updating leaflet map view without updating the props
        map.map.setView([50.0, 20.0], 15);
        expect(map.map.getZoom()).toBe(15);
        expect(map.map.getCenter().lng).toBe(20.0);
        expect(map.map.getCenter().lat).toBe(50.0);

        // setup some spyes to detect changes in leaflet map view
        const setViewSpy = expect.spyOn(map.map, "setView").andCallThrough();

        // since the props are the same no view changes should happend
        map = ReactDOM.render(<LeafletMap id="mymap" center={{y: 40.0, x: 10.0}} zoom={10}/>,
                        document.getElementById("container"));
        expect(setViewSpy.calls.length).toBe(0);

        // the view view should not be updated since new props are equal to map values
        map = ReactDOM.render(<LeafletMap id="mymap" center={{y: 50.0, x: 20.0}} zoom={15}/>,
                        document.getElementById("container"));
        expect(setViewSpy.calls.length).toBe(0);

        // the zoom and center values should be udpated
        map = ReactDOM.render(<LeafletMap id="mymap" center={{y: 40.0, x: 10.0}} zoom={10}/>,
                        document.getElementById("container"));
        expect(setViewSpy.calls.length).toBe(1);
        expect(map.map.getZoom()).toBe(10);
        expect(map.map.getCenter().lng).toBe(10.0);
        expect(map.map.getCenter().lat).toBe(40.0);
    });

    it('test GET_PIXEL_FROM_COORDINATES_HOOK/GET_COORDINATES_FROM_PIXEL_HOOK hook registration', () => {
        mapUtils.registerHook(mapUtils.GET_PIXEL_FROM_COORDINATES_HOOK, undefined);
        mapUtils.registerHook(mapUtils.GET_COORDINATES_FROM_PIXEL_HOOK, undefined);
        let getPixelFromCoordinates = mapUtils.getHook(mapUtils.GET_PIXEL_FROM_COORDINATES_HOOK);
        let getCoordinatesFromPixel = mapUtils.getHook(mapUtils.GET_COORDINATES_FROM_PIXEL_HOOK);
        expect(getPixelFromCoordinates).toNotExist();
        expect(getCoordinatesFromPixel).toNotExist();

        const map = ReactDOM.render(<LeafletMap id="mymap" center={{y: 0, x: 0}} zoom={11} registerHooks={true}/>,
                                    document.getElementById("container"));
        expect(map).toExist();

        getPixelFromCoordinates = mapUtils.getHook(mapUtils.GET_PIXEL_FROM_COORDINATES_HOOK);
        getCoordinatesFromPixel = mapUtils.getHook(mapUtils.GET_COORDINATES_FROM_PIXEL_HOOK);
        expect(getPixelFromCoordinates).toExist();
        expect(getCoordinatesFromPixel).toExist();
    });

});
