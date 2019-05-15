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

const {isArray} = require('lodash');

const parseUrl = (url) => {
    const parsed = urlUtil.parse(url, true);
    return urlUtil.format(assign({}, parsed, {search: null}, {
        query: assign({
            service: "WMS",
            version: "1.3.0",
            request: "GetCapabilities"
        }, parsed.query)
    }));
};

const flatLayers = (root) => {
    return root.Layer ? (isArray(root.Layer) && root.Layer || [root.Layer]).reduce((previous, current) => {
        return previous.concat(flatLayers(current)).concat((current.Layer && current.Name) ? [current] : []);
    }, []) : (root.Name && [root] || []);
};
const getOnlineResource = (c) => {
    return c.Request && c.Request.GetMap && c.Request.GetMap.DCPType && c.Request.GetMap.DCPType.HTTP && c.Request.GetMap.DCPType.HTTP.Get && c.Request.GetMap.DCPType.HTTP.Get.OnlineResource && c.Request.GetMap.DCPType.HTTP.Get.OnlineResource.$ || undefined;
};
const searchAndPaginate = (json, startPosition, maxRecords, text) => {
    const root = (json.WMS_Capabilities || json.WMT_MS_Capabilities).Capability;
    const onlineResource = getOnlineResource(root);
    const SRSList = (root.Layer && (root.Layer.SRS || root.Layer.CRS)) || [];
    const layersObj = flatLayers(root);
    const layers = isArray(layersObj) ? layersObj : [layersObj];
    const filteredLayers = layers
        .filter((layer) => !text || layer.Name.toLowerCase().indexOf(text.toLowerCase()) !== -1 || (layer.Title && layer.Title.toLowerCase().indexOf(text.toLowerCase()) !== -1) || (layer.Abstract && layer.Abstract.toLowerCase().indexOf(text.toLowerCase()) !== -1));
    return {
        numberOfRecordsMatched: filteredLayers.length,
        numberOfRecordsReturned: Math.min(maxRecords, filteredLayers.length),
        nextRecord: startPosition + Math.min(maxRecords, filteredLayers.length) + 1,
        service: json.WMS_Capabilities.Service,
        records: filteredLayers
            .filter((layer, index) => index >= (startPosition - 1) && index < (startPosition - 1) + maxRecords)
            .map((layer) => assign({}, layer, {onlineResource, SRS: SRSList}))
    };
};

const Api = {
    getCapabilities: function(url) {
        const parsed = urlUtil.parse(url, true);
        const getCapabilitiesUrl = urlUtil.format(assign({}, parsed, {
            query: assign({
                service: "WMS",
                version: "1.1.1",
                request: "GetCapabilities"
            }, parsed.query)
        }));
        return new Promise((resolve) => {
            require.ensure(['../utils/ogc/WMS'], () => {
                const {unmarshaller} = require('../utils/ogc/WMS');
                resolve(axios.get(parseUrl(getCapabilitiesUrl)).then((response) => {
                    let json = unmarshaller.unmarshalString(response.data);
                    return json && json.value;
                }));
            });
        });
    },
    describeLayer: function(url, layers) {
        const parsed = urlUtil.parse(url, true);
        const describeLayerUrl = urlUtil.format(assign({}, parsed, {
            query: assign({
                service: "WMS",
                version: "1.1.1",
                layers: layers,
                request: "DescribeLayer"
            }, parsed.query)
        }));
        return new Promise((resolve) => {
            require.ensure(['../utils/ogc/WMS'], () => {
                const {unmarshaller} = require('../utils/ogc/WMS');
                resolve(axios.get(parseUrl(describeLayerUrl)).then((response) => {
                    let json = unmarshaller.unmarshalString(response.data);
                    return json && json.value && json.value.layerDescription && json.value.layerDescription[0];

                }));
            });
        });
    },
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
    describeLayers: function(url, layers) {
        const parsed = urlUtil.parse(url, true);
        const describeLayerUrl = urlUtil.format(assign({}, parsed, {
            query: assign({
                service: "WMS",
                version: "1.1.1",
                layers: layers,
                request: "DescribeLayer"
            }, parsed.query)
        }));
        return axios.get(parseUrl(describeLayerUrl)).then((response) => {
            let decriptions;
            xml2js.parseString(response.data, {explicitArray: false}, (ignore, result) => {
                decriptions = result && result.WMS_DescribeLayerResponse && result.WMS_DescribeLayerResponse.LayerDescription;
            });
            decriptions = Array.isArray(decriptions) ? decriptions : [decriptions];
            // make it compatible with json format of describe layer
            return decriptions.map(desc => ({
                ...(desc && desc.$ || {}),
                layerName: desc.$ && desc.$.name,
                query: {
                    ...(desc && desc.query && desc.query.$ || {})
                }
            }));
        });
    },
    textSearch: function(url, startPosition, maxRecords, text) {
        return Api.getRecords(url, startPosition, maxRecords, text);
    }
};

module.exports = Api;
