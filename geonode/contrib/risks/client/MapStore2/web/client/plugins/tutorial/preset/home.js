/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

module.exports = [
    // add Tutorial plugin to homepage, "maps" in localConfig with cfg: {preset: "home"}
    // remove comment to enable intro/autostart
    /*{
        translation: 'intro',
        selector: '#intro-tutorial'
    },*/
    {
        translation: 'mapType',
        selector: '#mapstore-maptype',
        position: 'top'
    },
    {
        translation: 'mapsGrid',
        selector: '#mapstore-maps-grid',
        position: 'top'
    },
    {
        translation: 'examples',
        selector: '#mapstore-examples-applications',
        position: 'top'
    }
];
