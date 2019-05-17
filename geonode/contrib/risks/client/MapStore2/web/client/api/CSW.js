/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const axios = require('../libs/ajax');

const _ = require('lodash');

const urlUtil = require('url');
const assign = require('object-assign');

const parseUrl = (url) => {
    const parsed = urlUtil.parse(url, true);
    return urlUtil.format(assign({}, parsed, {search: null}, {
        query: assign({
            service: "CSW",
            version: "2.0.2"
        }, parsed.query, {request: undefined})
    }));
};

/**
 * API for local config
 */
var Api = {
    getRecords: function(url, startPosition, maxRecords, filter) {
        return new Promise((resolve) => {
            require.ensure(['../utils/ogc/CSW', '../utils/ogc/Filter'], () => {
                const {CSW, marshaller, unmarshaller} = require('../utils/ogc/CSW');

                let body = marshaller.marshalString({
                    name: "csw:GetRecords",
                    value: CSW.getRecords(startPosition, maxRecords, filter)
                });
                resolve(axios.post(parseUrl(url), body, { headers: {
                    'Content-Type': 'application/xml'
                }}).then(
                    (response) => {
                        if (response ) {
                            let json = unmarshaller.unmarshalString(response.data);
                            if (json && json.name && json.name.localPart === "GetRecordsResponse" && json.value && json.value.searchResults) {
                                let rawResult = json.value;
                                let rawRecords = rawResult.searchResults.abstractRecord || rawResult.searchResults.any;
                                let result = {
                                    numberOfRecordsMatched: rawResult.searchResults.numberOfRecordsMatched,
                                    numberOfRecordsReturned: rawResult.searchResults.numberOfRecordsReturned,
                                    nextRecord: rawResult.searchResults.nextRecord
                                    // searchStatus: rawResult.searchStatus
                                };
                                let records = [];
                                if (rawRecords) {
                                    for (let i = 0; i < rawRecords.length; i++) {
                                        let rawRec = rawRecords[i].value;
                                        let obj = {
                                            dateStamp: rawRec.dateStamp && rawRec.dateStamp.date,
                                            fileIdentifier: rawRec.fileIdentifier && rawRec.fileIdentifier.characterString && rawRec.fileIdentifier.characterString.value,
                                            identificationInfo: rawRec.abstractMDIdentification && rawRec.abstractMDIdentification.value
                                        };
                                        if (rawRec.boundingBox) {
                                            let bbox;
                                            let crs;
                                            let el;
                                            if (Array.isArray(rawRec.boundingBox)) {
                                                el = _.head(rawRec.boundingBox);
                                            } else {
                                                el = rawRec.boundingBox;
                                            }
                                            if (el && el.value) {
                                                let lc = el.value.lowerCorner;
                                                let uc = el.value.upperCorner;
                                                bbox = [lc[1], lc[0], uc[1], uc[0]];
                                                // TODO parse the extent's crs
                                                let crsCode = el.value && el.value.crs && el.value.crs.split(":::")[1];
                                                if (crsCode === "WGS 1984") {
                                                    crs = "EPSG:4326";
                                                } else if (crsCode) {
                                                    // TODO check is valid EPSG code
                                                    crs = "EPSG:" + crsCode;
                                                } else {
                                                    crs = "EPSG:4326";
                                                }
                                            }
                                            obj.boundingBox = {
                                                extent: bbox,
                                                crs: crs
                                            };
                                        }
                                        let dcElement = rawRec.dcElement;
                                        if (dcElement) {
                                            let dc = {
                                                references: []
                                            };
                                            for (let j = 0; j < dcElement.length; j++) {
                                                let dcel = dcElement[j];
                                                let elName = dcel.name.localPart;
                                                let finalEl = {};
                                                /* Some services (e.g. GeoServer ) support http://schemas.opengis.net/csw/2.0.2/record.xsd only
                                                * Usually they publish the WMS URL at dct:"references" with scheme=OGC:WMS
                                                * So we place references as they are.
                                                */
                                                if (elName === "references" && dcel.value) {
                                                    let urlString = dcel.value.content && dcel.value.content[0] || dcel.value.content || dcel.value;
                                                    finalEl = {
                                                        value: urlString,
                                                        scheme: dcel.value.scheme
                                                    };
                                                } else {
                                                    finalEl = dcel.value.content && dcel.value.content[0] || dcel.value.content || dcel.value;
                                                }
                                                if (dc[elName] && Array.isArray(dc[elName])) {
                                                    dc[elName].push(finalEl);
                                                } else if (dc[elName]) {
                                                    dc[elName] = [dc[elName], finalEl];
                                                } else {
                                                    dc[elName] = finalEl;
                                                }
                                            }
                                            obj.dc = dc;
                                        }
                                        records.push(obj);
                                    }
                                }
                                result.records = records;
                                return result;
                            } else if (json && json.name && json.name.localPart === "ExceptionReport") {
                                return {
                                    error: json.value.exception && json.value.exception.length && json.value.exception[0].exceptionText || 'GenericError'
                                };
                            }
                        }
                        return null;
                    }));
            });
        });
    },
    textSearch: function(url, startPosition, maxRecords, text) {
        return new Promise((resolve) => {
            require.ensure(['../utils/ogc/CSW', '../utils/ogc/Filter'], () => {
                const {Filter} = require('../utils/ogc/Filter');
                // creates a request like this:
                // <ogc:PropertyName>apiso:AnyText</ogc:PropertyName><ogc:Literal>%a%</ogc:Literal></ogc:PropertyIsLike>
                let filter = null;
                if (text) {
                    let ops = Filter.propertyIsLike("csw:AnyText", "%" + text + "%");
                    filter = Filter.filter(ops);
                }
                resolve(Api.getRecords(url, startPosition, maxRecords, filter));
            });
        });
    },
    workspaceSearch: function(url, startPosition, maxRecords, text, workspace) {
        return new Promise((resolve) => {
            require.ensure(['../utils/ogc/CSW', '../utils/ogc/Filter'], () => {
                const {Filter} = require('../utils/ogc/Filter');
                const workspaceTerm = workspace || "%";
                const layerNameTerm = text && "%" + text + "%" || "%";
                const ops = Filter.propertyIsLike("identifier", workspaceTerm + ":" + layerNameTerm);
                const filter = Filter.filter(ops);
                resolve(Api.getRecords(url, startPosition, maxRecords, filter));
            });
        });
    }
};

module.exports = Api;
