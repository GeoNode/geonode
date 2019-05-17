/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var {
    ERROR_FEATURE_INFO,
    EXCEPTIONS_FEATURE_INFO,
    LOAD_FEATURE_INFO,
    CHANGE_MAPINFO_STATE,
    NEW_MAPINFO_REQUEST,
    PURGE_MAPINFO_RESULTS,
    CHANGE_MAPINFO_FORMAT,
    SHOW_REVERSE_GEOCODE,
    HIDE_REVERSE_GEOCODE,
    GET_VECTOR_INFO,
    getFeatureInfo,
    changeMapInfoState,
    newMapInfoRequest,
    purgeMapInfoResults,
    changeMapInfoFormat,
    showMapinfoRevGeocode,
    hideMapinfoRevGeocode,
    getVectorInfo
} = require('../mapInfo');

describe('Test correctness of the map actions', () => {

    it('get feature info data', (done) => {
        /*eslint-disable */
        let reqId;
        /*eslint-enable */
        getFeatureInfo('base/web/client/test-resources/featureInfo-response.json', {p: "p"}, "meta")((e) => {
            if (e.type === NEW_MAPINFO_REQUEST) {
                reqId = e.reqId;
                try {
                    expect(e).toExist();
                    expect(e.type).toBe(NEW_MAPINFO_REQUEST);
                    expect(e.reqId).toExist();
                    expect(e.request).toExist();
                    expect(e.request.p).toBe("p");
                } catch(ex) {
                    done(ex);
                }
            } else if (e.type === LOAD_FEATURE_INFO) {
                try {
                    expect(e).toExist();
                    expect(e.type).toBe(LOAD_FEATURE_INFO);
                    expect(e.data).toExist();
                    expect(e.requestParams).toExist();
                    expect(e.reqId).toExist();
                    expect(e.reqId).toBe(reqId);
                    expect(e.requestParams.p).toBe("p");
                    expect(e.layerMetadata).toBe("meta");
                    done();
                } catch(ex) {
                    done(ex);
                }
            }
        });
    });

    it('get feature info exception', (done) => {
            /*eslint-disable */
            let reqId;
            /*eslint-enable */
        getFeatureInfo('base/web/client/test-resources/featureInfo-exception.json', {p: "p"}, "meta")((e) => {
            if (e.type === NEW_MAPINFO_REQUEST) {
                reqId = e.reqId;
                try {
                    expect(e).toExist();
                    expect(e.type).toBe(NEW_MAPINFO_REQUEST);
                    expect(e.reqId).toExist();
                    expect(e.request).toExist();
                    expect(e.request.p).toBe("p");
                } catch(ex) {
                    done(ex);
                }
            } else if (e.type === EXCEPTIONS_FEATURE_INFO) {
                try {
                    expect(e).toExist();
                    expect(e.type).toBe(EXCEPTIONS_FEATURE_INFO);
                    expect(e.exceptions).toExist();
                    expect(e.reqId).toExist();
                    expect(e.reqId).toBe(reqId);
                    expect(e.requestParams).toExist();
                    expect(e.requestParams.p).toBe("p");
                    expect(e.layerMetadata).toBe("meta");
                    done();
                } catch(ex) {
                    done(ex);
                }
            }
        });
    });

    it('get feature info error', (done) => {
        /*eslint-disable */
        let reqId;
        /*eslint-enable */
        getFeatureInfo('requestError.json', {p: "p"}, "meta")((e) => {
            if (e.type === NEW_MAPINFO_REQUEST) {
                reqId = e.reqId;
                try {
                    expect(e).toExist();
                    expect(e.type).toBe(NEW_MAPINFO_REQUEST);
                    expect(e.reqId).toExist();
                    expect(e.request).toExist();
                    expect(e.request.p).toBe("p");
                } catch(ex) {
                    done(ex);
                }
            } else if (e.type === ERROR_FEATURE_INFO) {
                try {
                    expect(e).toExist();
                    expect(e.type).toBe(ERROR_FEATURE_INFO);
                    expect(e.error).toExist();
                    expect(e.reqId).toExist();
                    expect(e.reqId).toBe(reqId);
                    expect(e.requestParams).toExist();
                    expect(e.requestParams.p).toBe("p");
                    expect(e.layerMetadata).toBe("meta");
                    done();
                } catch(ex) {
                    done(ex);
                }
            }
        });
    });

    it('gets vector info', () => {
        const retval = getVectorInfo('layer', 'request', 'metadata');

        expect(retval.type).toBe(GET_VECTOR_INFO);
        expect(retval.layer).toBe('layer');
        expect(retval.request).toBe('request');
        expect(retval.metadata).toBe('metadata');
    });

    it('change map info state', () => {
        const testVal = "val";
        const retval = changeMapInfoState(testVal);

        expect(retval.type).toBe(CHANGE_MAPINFO_STATE);
        expect(retval.enabled).toExist();
        expect(retval.enabled).toBe(testVal);
    });

    it('add new info request', () => {
        const reqIdVal = 100;
        const requestVal = {p: "p"};
        const e = newMapInfoRequest(reqIdVal, requestVal);
        expect(e).toExist();
        expect(e.type).toBe(NEW_MAPINFO_REQUEST);
        expect(e.reqId).toExist();
        expect(e.reqId).toBeA('number');
        expect(e.reqId).toBe(100);
        expect(e.request).toExist();
        expect(e.request.p).toBe("p");
    });

    it('delete all results', () => {
        const retval = purgeMapInfoResults();

        expect(retval.type).toBe(PURGE_MAPINFO_RESULTS);
    });

    it('change mapInfo format', () => {
        const retval = changeMapInfoFormat('testFormat');

        expect(retval.type).toBe(CHANGE_MAPINFO_FORMAT);
        expect(retval.infoFormat).toBe('testFormat');
    });

    it('get reverse geocode data', () => {
        let placeId;
        showMapinfoRevGeocode({lat: 40, lng: 10})((e) => {
            placeId = e.reverseGeocodeData.place_id;
            expect(e).toExist();
            expect(e.type).toBe(SHOW_REVERSE_GEOCODE);
            expect(placeId).toExist();
        });
    });

    it('reset reverse geocode data', () => {
        const e = hideMapinfoRevGeocode();
        expect(e).toExist();
        expect(e.type).toBe(HIDE_REVERSE_GEOCODE);
    });
});
