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
        // DC_1_1,
        DCT,
        SMIL_2_0,
        SMIL_2_0_Language,
        GML_3_1_1,
        Filter_1_1_0,
        CSW_2_0_2,
        GML_3_2_0,
        GML_3_2_1,
        ISO19139_GCO_20070417,
        ISO19139_GMD_20070417,
        ISO19139_GMX_20070417,
        ISO19139_GSS_20070417,
        ISO19139_GTS_20070417,
        ISO19139_GSR_20070417,
        ISO19139_2_GMI_1_0
} = require('ogc-schemas');
const DC_1_1 = require('./DC_1_1_full');
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
    CSW_2_0_2,
    GML_3_2_0,
    GML_3_2_1,
    ISO19139_GCO_20070417,
    ISO19139_GMD_20070417,
    ISO19139_GMX_20070417,
    ISO19139_GSS_20070417,
    ISO19139_GTS_20070417,
    ISO19139_GSR_20070417,
    ISO19139_2_GMI_1_0], {
    namespacePrefixes: {
        "http://www.opengis.net/cat/csw/2.0.2": "csw",
        "http://www.opengis.net/ogc": 'ogc',
        "http://www.opengis.net/gml": "gml",
        "http://purl.org/dc/elements/1.1/": "dc",
        "http://purl.org/dc/terms/": "dct",
        "http://www.isotc211.org/2005/gmd": "gmd",
        "http://www.isotc211.org/2005/gco": "gco",
        "http://www.isotc211.org/2005/gmi": "gmi",
        "http://www.opengis.net/ows": "ows"
    }
});
/*eslint-enable */
const marshaller = context.createMarshaller();
const unmarshaller = context.createUnmarshaller();
const CSW = {
    getRecords: function(startPosition, maxRecords, query, outputSchema) {
        let body = {
            startPosition: startPosition,
            maxRecords: maxRecords,
            abstractQuery: CSW.query("full", query && CSW.constraint(query)),
            resultType: "results",
            service: "CSW",
            version: "2.0.2"
        };
        if (outputSchema) {
            body.outputSchema = outputSchema;
        }
        return body;
    },
    getRecordById: function(ids) {
        return {
            TYPE_NAME: "CSW_2_0_2.GetRecordByIdType",
            elementSetName: {
                ObjectTYPE_NAME: "CSW_2_0_2.ElementSetNameType",
                value: "full"
            },
            id: Array.isArray(ids) ? ids : [ids],
            service: "CSW",
            version: "2.0.2"
        };
    },
    query: function(elementSetName = "full", constraint) {
        let query = {
            "csw:Query": {
                TYPE_NAME: "CSW_2_0_2.QueryType",
                elementSetName: {
                    TYPE_NAME: "CSW_2_0_2.ElementSetNameType",
                    value: elementSetName
                },
                typeNames: [
                    {
                        key: "{http://www.opengis.net/cat/csw/2.0.2}Record",
                        localPart: "Record",
                        namespaceURI: "http://www.opengis.net/cat/csw/2.0.2",
                        prefix: "csw",
                        string: "{http://www.opengis.net/cat/csw/2.0.2}csw:Record"
                    }
                ]
            }
        };
        if (constraint) {
            query['csw:Query'].constraint = constraint;
        }
        return query;
    },
    constraint: (ogcfilter) => {
        return {
            TYPE_NAME: "CSW_2_0_2.QueryConstraintType",
            version: "1.1.0",
            "filter": ogcfilter
        };
    }
};


module.exports = {CSW, marshaller, unmarshaller};
