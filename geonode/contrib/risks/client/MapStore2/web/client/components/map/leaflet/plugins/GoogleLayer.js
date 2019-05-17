/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var Layers = require('../../../../utils/leaflet/Layers');
var Google = require('leaflet-plugins/layer/tile/Google');

Layers.registerType('google', (options) => {
    return new Google(options.name, {zoomOffset: options.zoomOffset || 0});
});
