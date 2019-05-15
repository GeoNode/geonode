/**
* Copyright 2016, GeoSolutions Sas.
* All rights reserved.
*
* This source code is licensed under the BSD-style license found in the
* LICENSE file in the root directory of this source tree.
*/

module.exports = {
    currentLayouts: (state) => state.print && state.print.capabilities &&
        state.print.capabilities.layouts.filter((layout) => layout.name.indexOf(state.print.spec.sheet) === 0) || [],
    twoPageEnabled: (state) => state.print && state.print.spec && state.print.spec.includeLegend
};
