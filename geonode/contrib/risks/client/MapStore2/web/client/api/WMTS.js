/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const axios = require('../libs/ajax');
const ConfigUtils = require('../utils/ConfigUtils');

const urlUtil = require('url');
const assign = require('object-assign');

const xml2js = require('xml2js');

const capabilitiesCache = {};

const {isArray, head} = require('lodash');

const {castArray} = require('lodash');

const CoordinatesUtils = require('../utils/CoordinatesUtils');

const parseUrl = (url) => {
    const parsed = urlUtil.parse(url, true);
    return urlUtil.format(assign({}, parsed, {search: null}, {
        query: assign({
            SERVICE: "WMTS",
            VERSION: "1.0.0",
            REQUEST: "getcapabilities"
        }, parsed.query)
    }));
};

const flatLayers = (root) => {
    return root.Layer ? (isArray(root.Layer) && root.Layer || [root.Layer]).reduce((previous, current) => {
        return previous.concat(flatLayers(current)).concat((current.Layer && current["ows:Identifier"]) ? [current] : []);
    }, []) : (root.ows.Title && [root] || []);
};

const getOperation = (operations, name, type) => {
    return head(head(operations
            .filter((operation) => operation.$.name === name)
            .map((operation) => castArray(operation["ows:DCP"]["ows:HTTP"]["ows:Get"])))
            .filter((request) => (request["ows:Constraint"] && request["ows:Constraint"]["ows:AllowedValues"]["ows:Value"]) === type)
            .map((request) => request.$["xlink:href"])
        );
};

const searchAndPaginate = (json, startPosition, maxRecords, text) => {
    const root = json.Capabilities.Contents;
    const operations = castArray(json.Capabilities["ows:OperationsMetadata"]["ows:Operation"]);
    const TileMatrixSet = (root.TileMatrixSet) || [];
    let SRSList = [];
    let len = TileMatrixSet.length;
    for (let i = 0; i < len; i++) {
        SRSList.push(CoordinatesUtils.getEPSGCode(TileMatrixSet[i]["ows:SupportedCRS"]));
    }
    const layersObj = root.Layer;
    const layers = castArray(layersObj);
    const filteredLayers = layers
        .filter((layer) => !text || layer["ows:Identifier"].toLowerCase().indexOf(text.toLowerCase()) !== -1 || (layer["ows:Title"] && layer["ows:Title"].toLowerCase().indexOf(text.toLowerCase()) !== -1));
    return {
        numberOfRecordsMatched: filteredLayers.length,
        numberOfRecordsReturned: Math.min(maxRecords, filteredLayers.length),
        nextRecord: startPosition + Math.min(maxRecords, filteredLayers.length) + 1,
        records: filteredLayers
            .filter((layer, index) => index >= (startPosition - 1) && index < (startPosition - 1) + maxRecords)
            .map((layer) => assign({}, layer, {SRS: SRSList, TileMatrixSet, GetTileUrl: getOperation(operations, "GetTile", "KVP")}))
    };
};

const Api = {
    getRecords: function(url, startPosition, maxRecords, text) {
        const cached = capabilitiesCache[url];
        if (cached && new Date().getTime() < cached.timestamp + (ConfigUtils.getConfigProp('cacheExpire') || 60) * 1000) {
            return new Promise((resolve) => {
                resolve(searchAndPaginate(cached.data, startPosition, maxRecords, text));
            });
        }
        return axios.get(parseUrl(url)).then((response) => {
            let json;
            xml2js.parseString(response.data, {explicitArray: false}, (ignore, result) => {
                json = result;
            });
            capabilitiesCache[url] = {
                timestamp: new Date().getTime(),
                data: json
            };
            return searchAndPaginate(json, startPosition, maxRecords, text);
        });
    },
    textSearch: function(url, startPosition, maxRecords, text) {
        return Api.getRecords(url, startPosition, maxRecords, text);
    }
};

module.exports = Api;
