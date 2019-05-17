/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');

var catalog = require('../catalog');
var {RECORD_LIST_LOADED, ADD_LAYER_ERROR} = require('../../actions/catalog');
const sampleRecord = {
    boundingBox: {
        extent: [10.686,
                44.931,
                46.693,
                12.54],
        crs: "EPSG:4326"

    },
    dc: {
        identifier: "test-identifier",
        title: "sample title",
        subject: ["subject1", "subject2"],
        "abstract": "sample abstract",
        URI: [{
            TYPE_NAME: "DC_1_1.URI",
            protocol: "OGC:WMS-1.1.1-http-get-map",
            name: "workspace:layername",
            description: "sample layer description",
            value: "http://wms.sample.service:80/geoserver/wms?SERVICE=WMS&"
        }, {
            TYPE_NAME: "DC_1_1.URI",
            protocol: "image/png",
            name: "thumbnail",
            value: "resources.get?id=187105&fname=55b9f7b9-53ff-4e2d-8537-4e681c3218c5_s.png&access=public"
        }]
    }
};
describe('Test the catalog reducer', () => {
    it('loads records from the catalog', () => {
        var state = catalog({}, {type: RECORD_LIST_LOADED, result: {records: [sampleRecord], searchOptions: {catalogURL: "test"}}});
        expect(state.hasOwnProperty('result')).toBe(true);
        expect(state.hasOwnProperty('searchOptions')).toBe(true);
    });

    it('handles layers error', () => {
        var state = catalog({}, {type: ADD_LAYER_ERROR, error: 'myerror'});
        expect(state.layerError).toBe('myerror');
    });
});
