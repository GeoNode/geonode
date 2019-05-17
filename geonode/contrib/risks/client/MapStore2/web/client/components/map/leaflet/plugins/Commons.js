/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

/**
 * Layer initializer for a tile source
 */
var L = require('leaflet');
module.exports = L.TileLayer.extend({
    initialize: function(options) {
        L.TileLayer.prototype.initialize.call(this, this.url, options);
    }
});
