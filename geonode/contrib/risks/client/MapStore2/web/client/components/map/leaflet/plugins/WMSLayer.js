/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const Layers = require('../../../../utils/leaflet/Layers');
const CoordinatesUtils = require('../../../../utils/CoordinatesUtils');
const WMSUtils = require('../../../../utils/leaflet/WMSUtils');
const L = require('leaflet');
const objectAssign = require('object-assign');
const {isArray, isEqual} = require('lodash');
const SecurityUtils = require('../../../../utils/SecurityUtils');


L.TileLayer.MultipleUrlWMS = L.TileLayer.WMS.extend({
    initialize: function(urls, options) {
        this._url = urls[0];
        this._urls = urls;

        this._urlsIndex = 0;

        let wmsParams = L.extend({}, this.defaultWmsParams);
        let tileSize = options.tileSize || this.options.tileSize;

        if (options.detectRetina && L.Browser.retina) {
            wmsParams.width = wmsParams.height = tileSize * 2;
        } else {
            wmsParams.width = wmsParams.height = tileSize;
        }

        for (let i in options) {
            // all keys that are not TileLayer options go to WMS params
            if (!this.options.hasOwnProperty(i) && i.toUpperCase() !== 'CRS') {
                wmsParams[i] = options[i];
            }
        }

        this.wmsParams = wmsParams;

        L.setOptions(this, options);
    },

    getTileUrl: function(tilePoint) { // (Point, Number) -> String
        let map = this._map;
        let tileSize = this.options.tileSize;

        let nwPoint = tilePoint.multiplyBy(tileSize);
        let sePoint = nwPoint.add([tileSize, tileSize]);

        let nw = this._crs.project(map.unproject(nwPoint, tilePoint.z));
        let se = this._crs.project(map.unproject(sePoint, tilePoint.z));
        let bbox = this._wmsVersion >= 1.3 && this._crs === L.CRS.EPSG4326 ?
            [se.y, nw.x, nw.y, se.x].join(',') :
            [nw.x, se.y, se.x, nw.y].join(',');
        this._urlsIndex++;
        if (this._urlsIndex === this._urls.length) {
            this._urlsIndex = 0;
        }
        const url = L.Util.template(this._urls[this._urlsIndex], {s: this._getSubdomain(tilePoint)});

        return url + L.Util.getParamString(this.wmsParams, url, true) + '&BBOX=' + bbox;
    }
});

L.tileLayer.multipleUrlWMS = function(urls, options) {
    return new L.TileLayer.MultipleUrlWMS(urls, options);
};

function wmsToLeafletOptions(options) {
    var opacity = options.opacity !== undefined ? options.opacity : 1;
    // NOTE: can we use opacity to manage visibility?
    return objectAssign({}, options.baseParams, {
        layers: options.name,
        styles: options.style || "",
        format: options.format || 'image/png',
        transparent: options.transparent !== undefined ? options.transparent : true,
        tiled: options.tiled !== undefined ? options.tiled : true,
        opacity: opacity,
        version: options.version || "1.3.0",
        SRS: CoordinatesUtils.normalizeSRS(options.srs || 'EPSG:3857', options.allowedSRS),
        CRS: CoordinatesUtils.normalizeSRS(options.srs || 'EPSG:3857', options.allowedSRS),
        tileSize: options.tileSize || 256
    }, options.params || {});
}

function getWMSURLs( urls ) {
    return urls.map((url) => url.split("\?")[0]);
}

Layers.registerType('wms', {
    create: (options) => {
        const urls = getWMSURLs(isArray(options.url) ? options.url : [options.url]);
        const queryParameters = wmsToLeafletOptions(options) || {};
        urls.forEach(url => SecurityUtils.addAuthenticationParameter(url, queryParameters));
        return L.tileLayer.multipleUrlWMS(urls, queryParameters);
    },
    update: function(layer, newOptions, oldOptions) {
        // find the options that make a parameter change
        let oldqueryParameters = WMSUtils.filterWMSParamOptions(wmsToLeafletOptions(oldOptions));
        let newQueryParameters = WMSUtils.filterWMSParamOptions(wmsToLeafletOptions(newOptions));
        let newParameters = Object.keys(newQueryParameters).filter((key) => {return newQueryParameters[key] !== oldqueryParameters[key]; });
        let newParams = {};
        if ( newParameters.length > 0 ) {
            newParameters.forEach( key => newParams[key] = newQueryParameters[key] );
            // set new options as parameters, merged with params
            layer.setParams(objectAssign(newParams, newParams.params, newOptions.params));
        } else if (!isEqual(newOptions.params, oldOptions.params)) {
            layer.setParams(newOptions.params);
        }
    }
});
