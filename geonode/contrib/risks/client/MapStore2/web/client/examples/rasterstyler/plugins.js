/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

module.exports = {
    plugins: {
        TOCPlugin: require('../../plugins/TOC'),
        MapPlugin: require('../../plugins/Map'),
        ToolbarPlugin: require('../../plugins/Toolbar'),
        SettingsPlugin: require('../../plugins/Settings'),
        MapLoadingPlugin: require('../../plugins/MapLoading'),
        RasterStylerPlugin: require('../../plugins/RasterStyler'),
        IdentifyPlugin: require('../../plugins/Identify')
    },
    requires: {}
};
