/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

module.exports = {
    plugins: {
        MapPlugin: require('../../MapStore2/web/client/plugins/Map'),
        TutorialPlugin: require('../../MapStore2/web/client/plugins/Tutorial'),
        TOCPlugin: require('../plugins/RiskTOC'),
        OmniBarPlugin: require('../../MapStore2/web/client/plugins/OmniBar'),
        IdenifyPlugin: require('../../MapStore2/web/client/plugins/Identify')
    },
    requires: {}
};
