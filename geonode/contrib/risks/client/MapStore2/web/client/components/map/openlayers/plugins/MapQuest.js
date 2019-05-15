/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var Layers = require('../../../../utils/openlayers/Layers');

Layers.registerType('mapquest', {
    create: (options) => {
        // MapQuest is not supported on OpenLayers
        options.onError();
        return false;
    },
    isValid: () => {
        // MapQuest is not supported on OpenLayers
        return false;
    }
});
