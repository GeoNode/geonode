/**
 * Copyright 2015-2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const mapInfo = require('../mapInfo');
const assign = require('object-assign');

require('babel-polyfill');

describe('Test the mapInfo reducer', () => {
    let appState = {requests: [{reqId: 10, request: "test"}]};

    it('returns original state on unrecognized action', () => {
        let state = mapInfo(1, {type: 'UNKNOWN'});
        expect(state).toBe(1);
    });

    it('creates a general error ', () => {
        let testAction = {
            type: 'ERROR_FEATURE_INFO',
            error: "error",
            requestParams: "params",
            layerMetadata: "meta",
            reqId: 10
        };

        let state = mapInfo( appState, testAction);
        expect(state.responses).toExist();
        expect(state.responses.length).toBe(1);
        expect(state.responses[0].response).toBe("error");
        expect(state.responses[0].queryParams).toBe("params");
        expect(state.responses[0].layerMetadata).toBe("meta");

        state = mapInfo(assign({}, appState, {responses: []}), testAction);
        expect(state.responses).toExist();
        expect(state.responses.length).toBe(1);
        expect(state.responses[0].response).toBe("error");
        expect(state.responses[0].queryParams).toBe("params");
        expect(state.responses[0].layerMetadata).toBe("meta");

        state = mapInfo(assign({}, appState, {responses: ["test"]}), testAction);
        expect(state.responses).toExist();
        expect(state.responses.length).toBe(2);
        expect(state.responses[0]).toBe("test");
        expect(state.responses[1].response).toBe("error");
        expect(state.responses[1].queryParams).toBe("params");
        expect(state.responses[1].layerMetadata).toBe("meta");
    });

    it('creates an wms feature info exception', () => {
        let testAction = {
            type: 'EXCEPTIONS_FEATURE_INFO',
            exceptions: "exception",
            requestParams: "params",
            layerMetadata: "meta",
            reqId: 10
        };

        let state = mapInfo(appState, testAction);
        expect(state.responses).toExist();
        expect(state.responses.length).toBe(1);
        expect(state.responses[0].response).toBe("exception");
        expect(state.responses[0].queryParams).toBe("params");
        expect(state.responses[0].layerMetadata).toBe("meta");

        state = mapInfo(assign({}, appState, {responses: []}), testAction);
        expect(state.responses).toExist();
        expect(state.responses.length).toBe(1);
        expect(state.responses[0].response).toBe("exception");
        expect(state.responses[0].queryParams).toBe("params");
        expect(state.responses[0].layerMetadata).toBe("meta");


        state = mapInfo(assign({}, appState, {responses: ["test"]}), testAction);
        expect(state.responses).toExist();
        expect(state.responses.length).toBe(2);
        expect(state.responses[0]).toBe("test");
        expect(state.responses[1].response).toBe("exception");
        expect(state.responses[1].queryParams).toBe("params");
        expect(state.responses[1].layerMetadata).toBe("meta");

    });

    it('creates a feature info data from succesfull request', () => {
        let testAction = {
            type: 'LOAD_FEATURE_INFO',
            data: "data",
            requestParams: "params",
            layerMetadata: "meta",
            reqId: 10
        };

        let state = mapInfo(appState, testAction);
        expect(state.responses).toExist();
        expect(state.responses.length).toBe(1);
        expect(state.responses[0].response).toBe("data");
        expect(state.responses[0].queryParams).toBe("params");
        expect(state.responses[0].layerMetadata).toBe("meta");

        state = mapInfo(assign({}, appState, {responses: []}), testAction);
        expect(state.responses).toExist();
        expect(state.responses.length).toBe(1);
        expect(state.responses[0].response).toBe("data");
        expect(state.responses[0].queryParams).toBe("params");
        expect(state.responses[0].layerMetadata).toBe("meta");

        state = mapInfo(assign({}, appState, {responses: ["test"]}), testAction);
        expect(state.responses).toExist();
        expect(state.responses.length).toBe(2);
        expect(state.responses[0]).toBe("test");
        expect(state.responses[1].response).toBe("data");
        expect(state.responses[1].queryParams).toBe("params");
        expect(state.responses[1].layerMetadata).toBe("meta");
    });

    it('creates a feature info data from vector info request', () => {
        let testAction = {
            type: 'GET_VECTOR_INFO',
            layer: {
                features: [{
                    "type": "Feature",
                     "geometry": {
                       "type": "Polygon",
                       "coordinates": [
                         [ [9.0, 42.0], [11.0, 42.0], [11.0, 44.0],
                           [9.0, 44.0], [9.0, 42.0] ]
                         ]
                     },
                     "properties": {
                       "prop0": "value0",
                       "prop1": {"this": "that"}
                     }
                }]
            },
            request: {
                lng: 10.0,
                lat: 43.0
            },
            metadata: "meta"
        };

        let state = mapInfo(appState, testAction);
        expect(state.responses).toExist();
        expect(state.responses.length).toBe(1);
        expect(state.responses[0].response).toExist();
        expect(state.responses[0].response.features.length).toBe(1);
        expect(state.responses[0].format).toBe('JSON');
        expect(state.responses[0].queryParams.lng).toBe(10.0);
        expect(state.responses[0].layerMetadata).toBe("meta");
    });

    it('creates a new mapinfo request', () => {
        let state = mapInfo({}, {type: 'NEW_MAPINFO_REQUEST', reqId: 1, request: "request"});
        expect(state.requests).toExist();
        expect(state.requests.length).toBe(1);
        expect(state.requests.filter((req) => req.reqId === 1)[0].request).toBe("request");

        state = mapInfo({requests: {} }, {type: 'NEW_MAPINFO_REQUEST', reqId: 1, request: "request"});
        expect(state.requests).toExist();
        expect(state.requests.length).toBe(1);
        expect(state.requests.filter((req) => req.reqId === 1)[0].request).toBe("request");

        state = mapInfo( appState, {type: 'NEW_MAPINFO_REQUEST', reqId: 1, request: "request"});

        expect(state.requests).toExist();
        expect(state.requests.length).toBe(2);
        expect(state.requests.filter((req) => req.reqId === 10)[0].request).toBe("test");
        expect(state.requests.filter((req) => req.reqId === 1)[0].request).toBe("request");
    });

    it('clear request queue', () => {
        let state = mapInfo({}, {type: 'PURGE_MAPINFO_RESULTS'});
        expect(state.responses).toExist();
        expect(state.responses.length).toBe(0);
        expect(state.requests).toExist();
        expect(state.requests.length).toBe(0);

        state = mapInfo(assign({}, appState, {responses: []}), {type: 'PURGE_MAPINFO_RESULTS'});
        expect(state.responses).toExist();
        expect(state.responses.length).toBe(0);
        expect(state.requests).toExist();
        expect(state.requests.length).toBe(0);

        state = mapInfo(assign({}, appState, {responses: ["test"]}), {type: 'PURGE_MAPINFO_RESULTS'});
        expect(state.responses).toExist();
        expect(state.responses.length).toBe(0);
        expect(state.requests).toExist();
        expect(state.requests.length).toBe(0);
    });

    it('set a new point on map which has been clicked', () => {
        let state = mapInfo({}, {type: 'CLICK_ON_MAP', point: "p"});
        expect(state.clickPoint).toExist();
        expect(state.clickPoint).toBe('p');

        state = mapInfo({clickPoint: 'oldP'}, {type: 'CLICK_ON_MAP', point: "p"});
        expect(state.clickPoint).toExist();
        expect(state.clickPoint).toBe('p');
    });

    it('enables map info', () => {
        let state = mapInfo({}, {type: 'CHANGE_MAPINFO_STATE', enabled: true});
        expect(state).toExist();
        expect(state.enabled).toBe(true);

        state = mapInfo({}, {type: 'CHANGE_MAPINFO_STATE', enabled: false});
        expect(state).toExist();
        expect(state.enabled).toBe(false);
    });

    it('change mapinfo format', () => {
        let state = mapInfo({}, {type: 'CHANGE_MAPINFO_FORMAT', infoFormat: "testFormat"});
        expect(state).toExist();
        expect(state.infoFormat).toBe("testFormat");

        state = mapInfo({infoFormat: 'oldFormat'}, {type: 'CHANGE_MAPINFO_FORMAT', infoFormat: "newFormat"});
        expect(state).toExist();
        expect(state.infoFormat).toBe('newFormat');
    });

    it('show reverese geocode', () => {
        let state = mapInfo({}, {type: 'SHOW_REVERSE_GEOCODE'});
        expect(state).toExist();
        expect(state.showModalReverse).toBe(true);

        state = mapInfo({reverseGeocodeData: {}}, {type: "SHOW_REVERSE_GEOCODE", reverseGeocodeData: "newData"});
        expect(state).toExist();
        expect(state.reverseGeocodeData).toBe('newData');
    });

    it('hide reverese geocode', () => {
        let state = mapInfo({}, {type: 'HIDE_REVERSE_GEOCODE'});
        expect(state).toExist();
        expect(state.showModalReverse).toBe(false);
        expect(state.reverseGeocodeData).toBe(undefined);
    });

    it('should reset the state', () => {
        let state = mapInfo({showMarker: true}, {type: 'RESET_CONTROLS'});
        expect(state).toExist();
        expect(state.showMarker).toBe(false);
    });

});
