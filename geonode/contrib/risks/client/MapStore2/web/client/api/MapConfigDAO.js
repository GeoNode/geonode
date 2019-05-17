/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var axios = require('../libs/ajax');
var ConfigUtils = require('../utils/ConfigUtils');
/**
 * API for local config
 */
var Api = {
    get: function(url) {
        return axios.get(url).then((response) => {
            return response.data;
        });
    },

    /**
     * Returns Merged configurations from base url and GeoStore
     */
    getMergedConfig: function(baseConfigURL, mapId, geoStoreBase) {
        var url = ( geoStoreBase || "/mapstore/rest/geostore/" ) + "data/" + mapId;
        if (!mapId) {
            return Api.get(baseConfigURL);
        }

        return axios.all([axios.get(baseConfigURL), axios.get(url)])
            .then( (args) => {
                var baseConfig = args[0].data;
                var mapConfig = args[1].data;
                return ConfigUtils.mergeConfigs(baseConfig, mapConfig);
            }).catch( () => {
                return Api.get(baseConfigURL);
            });
    }
};

module.exports = Api;
