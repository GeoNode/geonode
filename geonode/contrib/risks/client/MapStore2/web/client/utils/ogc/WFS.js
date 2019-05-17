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
        Filter_1_1_0,
        GML_3_1_1,
        SMIL_2_0,
        SMIL_2_0_Language,
        WFS_1_1_0
} = require('ogc-schemas');

const {XLink_1_0, XSD_1_0} = require('w3c-schemas');
const {Jsonix} = require('jsonix');
const context = new Jsonix.Context([
    XLink_1_0,
    XSD_1_0,
    OWS_1_0_0,
    Filter_1_1_0,
    GML_3_1_1,
    SMIL_2_0,
    SMIL_2_0_Language,
    WFS_1_1_0
],{
    namespacePrefixes: {
        "http://www.opengis.net/ogc": 'ogc',
        "http://www.opengis.net/wms": "wfs",
        "http://www.opengis.net/ows": "ows",
        "http://www.w3.org/2001/XMLSchema" : "xsd"
    }
});
/*eslint-enable */
const marshaller = context.createMarshaller();
const unmarshaller = context.createUnmarshaller();
const WFS = {};


module.exports = {WFS, marshaller, unmarshaller};
