/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var Layers = require('../../../../utils/leaflet/Layers');
const MQ = require('../../../../libs/mapquest');

Layers.registerType('mapquest', {
    create: (options) => {
        if (MQ) {
            return MQ.mapLayer(options);
        }
        if (options && options.onError) {
            options.onError();
        }
        return false;
    },
    isValid: () => {
        return MQ ? true : false;
    }
});
