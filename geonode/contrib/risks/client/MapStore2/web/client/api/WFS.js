/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const axios = require('../libs/ajax');

const urlUtil = require('url');
const assign = require('object-assign');

const Api = {
    /**
     * Simple getFeature using http GET method with json format
     */
    getFeatureSimple: function(baseUrl, params) {
        return axios.get(baseUrl + '?service=WFS&version=1.1.0&request=GetFeature', {
            params: assign({
                    service: "WFS",
                    version: "1.1.0",
                    request: "GetFeature",
                    format: "application/json"
                }, params)
        }).then((response) => {
            if (typeof response.data !== 'object') {
                return JSON.parse(response.data);
            }
            return response.data;
        });
    },
    describeFeatureType: function(url, typeName) {
        const parsed = urlUtil.parse(url, true);
        const describeLayerUrl = urlUtil.format(assign({}, parsed, {
            query: assign({
                service: "WFS",
                version: "1.1.0",
                typeName: typeName,
                request: "DescribeFeatureType"
            }, parsed.query)
        }));
        return new Promise((resolve) => {
            require.ensure(['../utils/ogc/WFS'], () => {
                const {unmarshaller} = require('../utils/ogc/WFS');
                resolve(axios.get(describeLayerUrl).then((response) => {
                    let json = unmarshaller.unmarshalString(response.data);
                    return json && json.value;

                }));
            });
        });
    }
};

module.exports = Api;
