/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const AgentUtils = {

    getWindowSize: function() {
        let width = window.innerWidth
                || document.documentElement.clientWidth
                || document.body.clientWidth;

        let height = window.innerHeight
                || document.documentElement.clientHeight
                || document.body.clientHeight;

        return {maxWidth: width, maxHeight: height};
    }

 };


module.exports = AgentUtils;
