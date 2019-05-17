/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

/** This HOOK is from https://github.com/Alpstein/leaflet-singleclick_0.7
 *  to handle the singleclick even. This fix is valid only for leaflet 0.7.*.
 *  Please change when upgrading as indicated in
 *  the github page above.
 */
var L = require('leaflet');

L.Map.addInitHook( function() {
    var that = this;
    var h;
    function clearH() {
        if (h !== null) {
            clearTimeout( h );
            h = null;
        }
    }
    if (that.on) {
        that.on( 'click', checkLater );
        that.on( 'dblclick', function() { setTimeout(clearH, 0 ); });
    }

    function checkLater( e ) {
        clearH();
        function check() {
            that.fire( 'singleclick', L.Util.extend( e, { type: 'singleclick' } ) );
        }
        h = setTimeout( check, 500 );
    }
});
