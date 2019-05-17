/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
// Disable ESLint because some of the names to include are not in camel case
/*eslint-disable */
// include base schemas and name spaces
const {
        OWS_1_0_0,
        WMS_1_0_0,
        WMS_1_1_0,
        WMS_1_1_1,
        WMS_1_3_0
} = require('ogc-schemas');

const XLink_1_0 = require('w3c-schemas').XLink_1_0;
const {Jsonix} = require('jsonix');
const context = new Jsonix.Context([
    OWS_1_0_0,
    XLink_1_0,
    WMS_1_0_0,
    WMS_1_1_0,
    WMS_1_1_1,
    WMS_1_3_0
    ], {
    namespacePrefixes: {
        "http://www.opengis.net/ogc": 'ogc',
        "http://www.opengis.net/wms": "wms",
        "http://purl.org/dc/elements/1.1/": "dc",
        "http://www.opengis.net/ows": "ows",
        "http://inspire.ec.europa.eu/schemas/inspire_vs/1.0": "inspire_vs",
        "http://inspire.ec.europa.eu/schemas/common/1.0": "inspire_common"
    }
});
/*eslint-enable */
const marshaller = context.createMarshaller();
const unmarshaller = context.createUnmarshaller();
const WMS = {};


module.exports = {WMS, marshaller, unmarshaller};
