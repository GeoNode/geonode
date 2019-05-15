/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const axios = require('../../libs/ajax');


var Api = {
    getImports: function(geoserverBaseUrl, options) {
        let url = geoserverBaseUrl + "imports";
        return axios.get(url, options);
    },
    createImport: function(geoserverBaseUrl, body, options) {
        let url = geoserverBaseUrl + "imports";
        return axios.post(url, body, options);
    },
    uploadImportFiles: function(geoserverBaseUrl, importId, files = [], options) {
        let url = geoserverBaseUrl + "imports/" + importId + "/tasks";
        let data = new FormData();
        files.forEach((file) => {data.append(file.name, file); });
        return axios.post(url, data, options);
    },
    loadImport: function(geoserverBaseUrl, importId, options) {
        let url = geoserverBaseUrl + "imports/" + importId;
        return axios.get(url, options);
    },
    updateTask: function( geoserverBaseUrl, importId, taskId, element, body, options) {
        let url = geoserverBaseUrl + "imports/" + importId + "/tasks/" + taskId;
        // element can be target, layer, transforms...
        if (element && element !== "task") {
            url += "/" + element;
        }
        return axios.put(url, body, options);
    },
    loadTask: function( geoserverBaseUrl, importId, taskId, options) {
        let url = geoserverBaseUrl + "imports/" + importId + "/tasks/" + taskId;
        return axios.get(url, options);
    },
    getTaskProgress: function( geoserverBaseUrl, importId, taskId, options) {
        let url = geoserverBaseUrl + "imports/" + importId + "/tasks/" + taskId + "/progress";
        return axios.get(url, options);
    },
    loadLayer: function( geoserverBaseUrl, importId, taskId, options) {
        let url = geoserverBaseUrl + "imports/" + importId + "/tasks/" + taskId + "/layer";
        return axios.get(url, options);
    },
    updateLayer: function( geoserverBaseUrl, importId, taskId, layer, options) {
        let url = geoserverBaseUrl + "imports/" + importId + "/tasks/" + taskId + "/layer";
        return axios.put(url, layer, options);
    },
    loadTarget: function( geoserverBaseUrl, importId, taskId, options) {
        let url = geoserverBaseUrl + "imports/" + importId + "/tasks/" + taskId + "/target";
        return axios.get(url, options);
    },
    runImport: function( geoserverBaseUrl, importId, options) {
        let url = geoserverBaseUrl + "imports/" + importId + "?async=true";
        return axios.post(url, null, options);
    },
    deleteImport: function(geoserverBaseUrl, importId, options) {
        let url = geoserverBaseUrl + "imports/" + importId;
        return axios.delete(url, options);
    },
    deleteTask: function(geoserverBaseUrl, importId, taskId, options) {
        let url = geoserverBaseUrl + "imports/" + importId + "/tasks/" + taskId;
        return axios.delete(url, options);
    },
    addTransform: function(geoserverBaseUrl, importId, taskId, transform, options) {
        let url = geoserverBaseUrl + "imports/" + importId + "/tasks/" + taskId + "/transforms";
        return axios.post(url, transform, options);
    },
    loadTransform: function(geoserverBaseUrl, importId, taskId, transformId, options) {
        let url = geoserverBaseUrl + "imports/" + importId + "/tasks/" + taskId + "/transforms/" + transformId;
        return axios.get(url, options);
    },
    updateTransform: function(geoserverBaseUrl, importId, taskId, transformId, transform, options) {
        let url = geoserverBaseUrl + "imports/" + importId + "/tasks/" + taskId + "/transforms/" + transformId;
        return axios.put(url, transform, options);
    },
    deleteTransform: function(geoserverBaseUrl, importId, taskId, transformId, options) {
        let url = geoserverBaseUrl + "imports/" + importId + "/tasks/" + taskId + "/transforms/" + transformId;
        return axios.delete(url, options);
    }
};

module.exports = Api;
