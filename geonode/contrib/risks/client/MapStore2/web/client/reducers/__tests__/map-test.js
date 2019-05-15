/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');

var mapConfig = require('../map');


describe('Test the map reducer', () => {
    it('returns original state on unrecognized action', () => {
        var state = mapConfig(1, {type: 'UNKNOWN'});
        expect(state).toBe(1);
    });

    it('return an updated state with new values for both zoom and center', () => {
        const oldState = {
            a: 'zero',
            zoom: 'zero',
            center: 'zero',
            projection: 'EPSG:4326'
        };
        var state = mapConfig(oldState, {
            type: 'CHANGE_MAP_VIEW',
            zoom: 0,
            center: 0,
            bbox: 0,
            size: 0,
            projection: 'EPSG:3857'
        });
        expect(state.a).toBe(oldState.a);
        expect(state.zoom).toBe(0);
        expect(state.center).toBe(0);
        expect(state.bbox).toBe(0);
        expect(state.size).toBe(0);
        expect(state.projection).toBe('EPSG:3857');
    });

    it('sets a new mouse pointer used over the map', () => {
        const action = {
            type: 'CHANGE_MOUSE_POINTER',
            pointer: "testPointer"
        };

        var state = mapConfig({}, action);
        expect(state.mousePointer).toBe(action.pointer);

        state = mapConfig({prop: 'prop'}, action);
        expect(state.prop).toBe('prop');
        expect(state.mousePointer).toBe(action.pointer);
    });

    it('sets a new zoom level', () => {
        const action = {
            type: 'CHANGE_ZOOM_LVL',
            zoom: 9
        };

        var state = mapConfig({}, action);
        expect(state.zoom).toBe(9);

        state = mapConfig({prop: 'prop'}, action);
        expect(state.prop).toBe('prop');
        expect(state.zoom).toBe(9);
    });

    it('sets a new crs', () => {
        const action = {
            type: 'CHANGE_MAP_CRS',
            crs: 'EPSG:4326'
        };

        var state = mapConfig({}, action);
        expect(state.projection).toBe('EPSG:4326');

        state = mapConfig({prop: 'prop'}, action);
        expect(state.prop).toBe('prop');
        expect(state.projection).toBe('EPSG:4326');
    });

    it('sets new map scales', () => {
        // set map scales
        const action = {
            type: 'CHANGE_MAP_SCALES',
            scales: [9600, 960]
        };
        const resolutions = [2.54, 0.254];
        const action2 = {
            type: 'CHANGE_MAP_SCALES',
            scales: [38400, 19200, 9600, 4800]
        };
        const resolutions2 = [10.16, 5.08, 2.54, 1.27];
        // reset map scales
        const actionReset = {
            type: 'CHANGE_MAP_SCALES'
        };

        // add map scales
        var state = mapConfig({projection: "EPSG:3857"}, action);
        expect(state.mapOptions).toExist();
        expect(state.mapOptions.view).toExist();
        expect(state.mapOptions.view.resolutions).toEqual(resolutions);
        expect(state.projection).toBe("EPSG:3857");

        // update map scales
        state = mapConfig(state, action2);
        expect(state.mapOptions).toExist();
        expect(state.mapOptions.view).toExist();
        expect(state.mapOptions.view.resolutions).toEqual(resolutions2);

        // remove state.mapOptions on map scales reset
        state = mapConfig({
            mapOptions: {
                view: {
                    resolutions: [8, 4, 2]
                }
            },
            prop: 'prop'
        }, actionReset);
        expect(state.mapOptions).toNotExist();
        expect(state.prop).toBe('prop');

        // remove only state.mapOptions.view on map scales reset
        state = mapConfig({
            mapOptions: {
                view: {
                    resolutions: [8, 4, 2]
                },
                prop: 'prop'
            }
        }, actionReset);
        expect(state.mapOptions).toExist();
        expect(state.mapOptions.view).toNotExist();
        expect(state.mapOptions.prop).toBe('prop');

        // remove only state.mapOptions.view.resolutions on map scales reset
        state = mapConfig({
            mapOptions: {
                view: {
                    resolutions: [8, 4, 2],
                    prop: 'prop'
                }
            }
        }, actionReset);
        expect(state.mapOptions).toExist();
        expect(state.mapOptions.view).toExist();
        expect(state.mapOptions.view.resolutions).toNotExist();
        expect(state.mapOptions.view.prop).toBe('prop');

        // add map scales with no initial state
        state = mapConfig(undefined, action);
        expect(state).toExist();
        expect(state.mapOptions).toExist();
        expect(state.mapOptions.view).toExist();
        expect(state.mapOptions.view.resolutions).toExist();
    });

    it('zoom to extent', () => {
        const action = {
            type: 'ZOOM_TO_EXTENT',
            extent: [10, 44, 12, 46],
            crs: "EPSG:4326"
        };
        // full extent
        const action2 = {
            type: 'ZOOM_TO_EXTENT',
            extent: [-180, -90, 180, 90],
            crs: "EPSG:4326"
        };

        var state = mapConfig({projection: "EPSG:4326", size: {width: 400, height: 400}}, action);
        expect(state.mapStateSource).toBe(undefined);
        expect(state.center.x).toBe(11);
        expect(state.center.y).toBe(45);
        expect(state.bbox).toExist();
        expect(state.bbox.bounds).toExist();
        expect(state.bbox.bounds.minx).toExist();
        expect(state.bbox.bounds.miny).toExist();
        expect(state.bbox.bounds.maxx).toExist();
        expect(state.bbox.bounds.maxy).toExist();
        state = mapConfig({projection: "EPSG:900913"}, action2);
        expect(state.zoom).toBe(1);
        expect(state.bbox).toExist();
        expect(state.bbox.bounds).toExist();
        expect(state.bbox.bounds.minx).toExist();
        expect(state.bbox.bounds.miny).toExist();
        expect(state.bbox.bounds.maxx).toExist();
        expect(state.bbox.bounds.maxy).toExist();

    });
    it('change map style', () => {
        const action = {
            type: 'CHANGE_MAP_STYLE',
            style: {width: 100},
            mapStateSource: "test"
        };
        var state = mapConfig({projection: "EPSG:4326"}, action);
        expect(state.mapStateSource).toBe("test");
        expect(state.style.width).toBe(100);
    });
    it('change map rotation', () => {
        let rotation = 0.5235987755982989;
        const action = {
            type: 'CHANGE_ROTATION',
            rotation: rotation,
            mapStateSource: "test"
        };
        let state = mapConfig({}, action);
        expect(state.bbox.rotation).toEqual(rotation);
        expect(state.mapStateSource).toBe("test");
    });
});
