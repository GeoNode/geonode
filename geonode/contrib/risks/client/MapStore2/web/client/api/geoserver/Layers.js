/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const axios = require('../../libs/ajax');

var Api = {
    getLayer: function(geoserverBaseUrl, layerName, options) {
        let url = geoserverBaseUrl + "layers/" + layerName + ".json";
        return axios.get(url, options).then((response) => {return response.data && response.data.layer; });
    }
};
module.exports = Api;
