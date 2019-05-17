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
    DC_1_1,
    DCT,
    SMIL_2_0,
    SMIL_2_0_Language,
    GML_3_1_1,
    Filter_1_1_0,
    CSW_2_0_2
} = require('ogc-schemas');
var XLink_1_0 = require('w3c-schemas').XLink_1_0;
const {Jsonix} = require('jsonix');
const context = new Jsonix.Context([
    OWS_1_0_0,
    DC_1_1,
    DCT,
    XLink_1_0,
    SMIL_2_0,
    SMIL_2_0_Language,
    GML_3_1_1,
    Filter_1_1_0,
    CSW_2_0_2], {
    namespacePrefixes: {
            'http://www.opengis.net/cat/csw/2.0.2': 'csw',
            "http://www.opengis.net/ogc": 'ogc',
            "http://www.opengis.net/gml": "gml",
            "http://www.opengis.net/ows": "ows"
        }
});
/*eslint-enable */
const marshaller = context.createMarshaller();
const unmarshaller = context.createUnmarshaller();
const Filter = {
    propertyName: function(propertyName) {
        return {
            PropertyName: propertyName
        };
    },
    propertyIsLike: function(propertyName, value) {
        return {
            'ogc:PropertyIsLike': {
                TYPE_NAME: "Filter_1_1_0.PropertyIsLikeType",
                escapeChar: "\\\\",
                singleChar: "_",
                wildCard: "%",
                literal: {
                    TYPE_NAME: "Filter_1_1_0.LiteralType",
                    content: [value]
                },
                propertyName: {
                    TYPE_NAME: "Filter_1_1_0.PropertyNameType",
                    content: [propertyName]
                }
            }
        };
    },
    bbox: function(llat, llon, ulat, ulon, srsName) {
        return {
            'ows:BBOX': {
                TYPE_NAME: "Filter_1_1_0.BBOXType",
                envelope: {
                    'gml:Envelope': {
                        TYPE_NAME: "GML_3_1_1.EnvelopeType",
                        lowerCorner: {
                            TYPE_NAME: "GML_3_1_1.DirectPositionType",
                            value: [llat, llon]
                        },
                        upperCorner: {
                            TYPE_NAME: "GML_3_1_1.DirectPositionType",
                            value: [ulat, ulon]
                        },
                        srsName: srsName
                    }
                }
            }
        };
    },
    and: function( opts ) {
        return {
            'ogc:And': {
                TYPE_NAME: "Filter_1_1_0.BinaryLogicOpType",
                ops: opts
            }
        };
    },
    or: function( opts ) {
        return {
            'ogc:Or': {
                TYPE_NAME: "Filter_1_1_0.BinaryLogicOpType",
                ops: opts
            }
        };
    },
    filter(logicOps, spatialOps) {
        return {
            "ogc:Filter": {
                TYPE_NAME: "Filter_1_1_0.FilterType",
                logicOps: logicOps,
                spatialOps: spatialOps
            }
        };
    }
};


module.exports = {Filter, marshaller, unmarshaller};
