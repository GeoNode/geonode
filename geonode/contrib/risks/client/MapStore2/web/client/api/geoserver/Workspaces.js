/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const axios = require('../../libs/ajax');


var Api = {
    getWorkspaces: function(geoserverRestURL) {
        return axios.get(geoserverRestURL + 'workspaces.json', {
            'headers': {
                'Accept': 'application/json'
            }
        }).then(function(response) {
            return response.data;
        });
    },
    createWorkspace: function(geoserverRestURL, name) {
        let body = {
            workspace: {
                name: name
            }
        };
        return axios.post(geoserverRestURL + 'workspaces', body, {
            'headers': {
                'Accept': 'application/json'
            }
        });
    },
    createDataStore: function(geoserverRestURL, workspace, datastore) {
        return axios.post(geoserverRestURL + 'workspaces/' + workspace + "/datastores.json", datastore, {
            'headers': {
                'Accept': 'application/json'
            }
        });
    }
};
module.exports = Api;
