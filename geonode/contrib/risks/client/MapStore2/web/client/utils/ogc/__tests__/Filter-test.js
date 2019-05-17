/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const {Filter, marshaller, unmarshaller} = require('../Filter');
/**
 * Validates CSW tag trying to unmarshal that
 */
const validate = function(body, localPart) {
    const doc = unmarshaller.unmarshalDocument(body);
    expect(doc).toExist();
    expect(doc.name && doc.name.localPart).toBe(localPart);
    return doc;
};
describe('Test Filter generation/parsing', () => {

    it('propertyIsLike', () => {
        expect(Filter.propertyIsLike).toExist();
        let jsonBody = Filter.propertyIsLike("propName", "%propValueLike%");
        expect(jsonBody).toExist();
        const doc = marshaller.marshalDocument( { name: "ogc:PropertyIsLike", value: jsonBody});
        expect(doc).toExist();
        let outJson = validate(doc, "PropertyIsLike");
        expect(outJson).toExist();
    });

    it('BBox', () => {
        expect(Filter.propertyIsLike).toExist();
        let jsonBody = Filter.bbox(0, 0, 1, 1, "EPSG:4326");
        expect(jsonBody).toExist();
        const doc = marshaller.marshalDocument( { name: "ogc:BBOX", value: jsonBody});
        expect(doc).toExist();
        validate(doc, "BBOX");
    });
    it('and', () => {
        expect(Filter.propertyIsLike).toExist();
        let json1 = Filter.propertyIsLike("propName", "%propValueLike%");
        expect(json1).toExist();
        let json2 = Filter.bbox(0, 0, 1, 1, "EPSG:4326");
        let and = Filter.and([json1, json2]);
        const doc = marshaller.marshalDocument( and );
        expect(doc).toExist();
        let outJson = validate(doc, "And");
        expect(outJson).toExist();
    });
    it('or', () => {
        expect(Filter.propertyIsLike).toExist();
        let json1 = Filter.propertyIsLike("propName", "%propValueLike%");
        expect(json1).toExist();
        let json2 = Filter.bbox(0, 0, 1, 1, "EPSG:4326");
        let or = Filter.or([json1, json2]);
        const doc = marshaller.marshalDocument( or );
        expect(doc).toExist();
        let outJson = validate(doc, "Or");
        expect(outJson).toExist();
    });
    it('Filter', () => {
        expect(Filter.propertyIsLike).toExist();
        let json1 = Filter.propertyIsLike("propName", "%propValueLike%");
        expect(json1).toExist();
        let json2 = Filter.bbox(0, 0, 1, 1, "EPSG:4326");
        let or = Filter.or([json1, json2]);
        let filter = Filter.filter(or);
        const doc = marshaller.marshalDocument( filter );
        expect(doc).toExist();
        let outJson = validate(doc, "Filter");
        expect(outJson).toExist();
    });

});
