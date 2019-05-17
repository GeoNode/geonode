/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const LayersUtils = require('../../utils/LayersUtils');
const {getRecords, addLayerError, addLayer, ADD_LAYER_ERROR} = require('../catalog');
const {CHANGE_LAYER_PROPERTIES, ADD_LAYER} = require('../layers');
describe('Test correctness of the catalog actions', () => {

    it('getRecords ISO Metadata Profile', (done) => {
        getRecords('csw', 'base/web/client/test-resources/csw/getRecordsResponseISO.xml', 1, 1)((actionResult) => {
            try {
                let result = actionResult && actionResult.result;
                expect(result).toExist();
                expect(result.records).toExist();
                expect(result.records.length).toBe(1);
                done();
            } catch(ex) {
                done(ex);
            }
        });
    });
    it('getRecords Error', (done) => {
        getRecords('csw', 'base/web/client/test-resources/csw/getRecordsResponseException.xml', 1, 1)((result) => {
            try {
                expect(result).toExist();
                expect(result.error).toExist();
                done();
            } catch(ex) {
                done(ex);
            }
        });
    });
    it('getRecords Dublin Core', (done) => {
        getRecords('csw', 'base/web/client/test-resources/csw/getRecordsResponseDC.xml', 1, 2)((actionResult) => {
            try {
                let result = actionResult && actionResult.result;
                expect(result).toExist();
                expect(result.records).toExist();
                expect(result.records.length).toBe(2);
                let rec0 = result.records[0];
                expect(rec0.dc).toExist();
                expect(rec0.dc.URI).toExist();
                expect(rec0.dc.URI[0]);
                let uri = rec0.dc.URI[0];
                expect(uri.name).toExist();
                expect(uri.value).toExist();
                expect(uri.description).toExist();
                done();
            } catch(ex) {
                done(ex);
            }
        });
    });
    it('add layer and describe it', (done) => {
        const verify = (action) => {
            if (action.type === ADD_LAYER) {
                expect(action.layer).toExist();
                const layer = action.layer;
                expect(layer.id).toExist();
                expect(layer.id).toBe(LayersUtils.getLayerId(action.layer, []));
            } else if (action.type === CHANGE_LAYER_PROPERTIES) {
                expect(action.layer).toExist();
                expect(action.newProperties).toExist();
                expect(action.newProperties.search).toExist();
                expect(action.newProperties.search.type ).toBe('wfs');
                expect(action.newProperties.search.url).toBe("http://some.geoserver.org:80/geoserver/wfs?");
                done();
            }
        };
        const callback = addLayer({
            url: 'base/web/client/test-resources/wms/DescribeLayers.xml',
            type: 'wms',
            name: 'workspace:vector_layer'
        });
        callback(verify, () => ({ layers: []}));
    });
    it('sets an error on addLayerError action', () => {
        const action = addLayerError('myerror');

        expect(action.type).toBe(ADD_LAYER_ERROR);
        expect(action.error).toBe('myerror');
    });
});
