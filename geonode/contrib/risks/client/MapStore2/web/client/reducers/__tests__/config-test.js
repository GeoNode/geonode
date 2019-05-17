/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');

var mapConfig = require('../config');


describe('Test the mapConfig reducer', () => {
    it('creates a configuration object from loaded config', () => {
        var state = mapConfig({}, {type: 'MAP_CONFIG_LOADED', config: { version: 2, map: { center: {x: 1, y: 1}, zoom: 11, layers: [] }}});
        expect(state.map).toExist();
        expect(state.map.zoom).toExist();
        expect(state.map.center).toExist();
        expect(state.map.center.crs).toExist();
        expect(state.layers).toExist();
    });

    it('creates a configuration object from legacy config', () => {
        var state = mapConfig({}, {type: 'MAP_CONFIG_LOADED', config: { map: { center: [1361886.8627049, 5723464.1181097], zoom: 11, layers: [] }}});
        expect(state.map).toExist();
        expect(state.map.zoom).toExist();
        expect(state.map.center).toExist();
        expect(state.map.center.crs).toExist();
        expect(state.layers).toExist();
    });

    it('checks if bing layer gets the apiKey', () => {
        var state = mapConfig({}, {type: 'MAP_CONFIG_LOADED', config: { version: 2, map: { center: {x: 1, y: 1}, zoom: 11, layers: [{type: 'bing'}] }}});
        expect(state.map.zoom).toExist();
        expect(state.map.center).toExist();
        expect(state.map.center.crs).toExist();
        expect(state.layers).toExist();
        expect(state.layers.length).toBe(1);
        expect(state.layers[0].apiKey).toBe(null);
    });

    it('creates an error on wrongly loaded config', () => {
        var state = mapConfig({}, {type: 'MAP_CONFIG_LOAD_ERROR', error: 'error'});
        expect(state.loadingError).toExist();
    });

    it('returns original state on unrecognized action', () => {
        var state = mapConfig(1, {type: 'UNKNOWN'});
        expect(state).toBe(1);
    });
    it('get map info', () => {
        var state = mapConfig({}, {type: 'MAP_CONFIG_LOADED', mapId: 1, config: { version: 2, map: {center: {x: 1, y: 1}, zoom: 11, layers: [] }}});
        state = mapConfig(state, {type: "MAP_INFO_LOAD_START", mapId: 1});
        expect(state.map).toExist();
        expect(state.map.info).toExist();
        expect(state.map.info.loading).toBe(true);
        expect(state.map.center.crs).toExist();
        state = mapConfig(state, {type: "MAP_INFO_LOADED", mapId: 1, info: {canEdit: true, canDelete: true}});
        expect(state.map).toExist();
        expect(state.map.info).toExist();
        expect(state.map.info.canEdit).toBe(true);
    });
});
