/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const Layers = require('../../../../utils/leaflet/Layers');
const SimpleGraticule = require('leaflet-simple-graticule/L.SimpleGraticule');
const assign = require('object-assign');

require('leaflet-simple-graticule/L.SimpleGraticule.css');

Layers.registerType('graticule', {
    create: (options) => {
        const graticuleOptions = assign({
            interval: 20,
            showOriginLabel: true,
            redraw: 'move'
        }, options);
        if (SimpleGraticule) {
            return new SimpleGraticule(graticuleOptions);
        }
        return null;
    },
    isValid: () => {
        return SimpleGraticule ? true : false;
    }
});
