/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const FileSaver = require('file-saver');
const toBlob = require('canvas-to-blob');
const shp = require('shpjs');

const FileUtils = {
    download: function(blob, name, mimetype) {
        let file = new Blob([blob], {type: mimetype});
        // a.href = URL.createObjectURL(file);
        FileSaver.saveAs(file, name);
    },
    downloadCanvasDataURL: function(dataURL, name, mimetype) {
        FileUtils.download(toBlob(dataURL), "snapshot.png", mimetype);
    },
    shpToGeoJSON: function(zipBuffer) {
        return [].concat(shp.parseZip(zipBuffer));
    },
    readZip: function(file) {
        return new Promise((resolve, reject) => {
            let reader = new FileReader();
            reader.onload = function() { resolve(reader.result); };
            reader.onerror = function() { reject(reader.error.name); };
            reader.readAsArrayBuffer(file);
        });

    }
};
module.exports = FileUtils;
