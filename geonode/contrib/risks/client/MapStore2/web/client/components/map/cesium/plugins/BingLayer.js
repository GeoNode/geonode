/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var Layers = require('../../../../utils/cesium/Layers');
var Cesium = require('../../../../libs/cesium');


Layers.registerType('bing', (options) => {
    var key = options.apiKey;
    return new Cesium.BingMapsImageryProvider({
        url: '//dev.virtualearth.net',
        key,
        mapStyle: Cesium.BingMapsStyle[options.name.toUpperCase()]
    });
});
