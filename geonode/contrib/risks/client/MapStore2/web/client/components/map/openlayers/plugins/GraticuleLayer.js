/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var Layers = require('../../../../utils/openlayers/Layers');
var ol = require('openlayers');


Layers.registerType('graticule', {
    create: (options, map) => {
        let graticule = new ol.Graticule({
          strokeStyle: options.style || new ol.style.Stroke({
            color: 'rgba(255,120,0,0.9)',
            width: 2,
            lineDash: [0.5, 4]
          })
        });
        graticule.setMap(map);

        return {
            detached: true,
            remove: () => {
                graticule.setMap(null);
            }
        };
    }
});
