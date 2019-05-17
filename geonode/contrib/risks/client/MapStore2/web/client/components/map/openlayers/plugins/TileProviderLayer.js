 /**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var assign = require('object-assign');
var Layers = require('../../../../utils/openlayers/Layers');
var ol = require('openlayers');
var TileProvider = require('../../../../utils/TileConfigProvider');
var CoordinatesUtils = require('../../../../utils/CoordinatesUtils');


function template(str, data) {

    return str.replace(/(?!(\{?[zyx]?\}))\{*([\w_]+)*\}/g, function() {
            let st = arguments[0];
            let key = arguments[1] ? arguments[1] : arguments[2];
            let value = data[key];

            if (value === undefined) {
                throw new Error('No value provided for variable ' + st);

            } else if (typeof value === 'function') {
                value = value(data);
            }
            return value;
        });
}
function getUrls(opt) {
    let urls = [];
    let url = opt.url;
    if (opt.subdomains) {
        for (let c of opt.subdomains) {
            urls.push(template(url.replace("{s}", c), opt));
        }
    } else {
        for (let c of 'abc') {
            urls.push(template(url.replace("{s}", c), opt));
        }
    }
    return urls;
}
/*eslint-disable */
function lBoundsToOlExtent(bounds, destPrj){
    var [ [ miny, minx], [ maxy, maxx ] ] = bounds;
    return CoordinatesUtils.reprojectBbox([minx, miny, maxx, maxy], 'EPSG:4326', CoordinatesUtils.normalizeSRS(destPrj));
}
/*eslint-enable */
function tileXYZToOpenlayersOptions(options) {
    let urls = (options.url.match(/(\{s\})/)) ? getUrls(options) : [template(options.url, options)];
    let sourceOpt = assign({}, {
                urls: urls,
                attributions: (options.attribution) ? [new ol.Attribution({ html: options.attribution})] : [],
                maxZoom: (options.maxZoom) ? options.maxZoom : 18,
                minZoom: (options.minZoom) ? options.minZoom : 0 // dosen't affect ol layer rendering UNSUPPORTED
            });
    let source = new ol.source.XYZ(sourceOpt);
    let olOpt = assign({}, {
                opacity: options.opacity !== undefined ? options.opacity : 1,
                visible: options.visibility !== false,
                zIndex: options.zIndex,
                source: source
                }, (options.bounds) ? {extent: lBoundsToOlExtent(options.bounds, options.srs ? options.srs : 'EPSG:3857')} : {} );
    return olOpt;
}

Layers.registerType('tileprovider', {
    create: (options) => {
        let [url, opt] = TileProvider.getLayerConfig(options.provider, options);
        opt.url = url;
        return new ol.layer.Tile(tileXYZToOpenlayersOptions(opt));
    }
});
