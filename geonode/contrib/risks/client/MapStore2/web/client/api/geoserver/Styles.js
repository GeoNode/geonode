/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const axios = require('../../libs/ajax');
const assign = require('object-assign');

var Api = {
    saveStyle: function(geoserverBaseUrl, styleName, body, options) {
        let url = geoserverBaseUrl + "styles/" + encodeURI(styleName);
        let opts = assign({}, options);
        opts.headers = assign({}, opts.headers, {"Content-Type": "application/vnd.ogc.sld+xml"});
        return axios.put(url, body, opts);
    }
};

module.exports = Api;
