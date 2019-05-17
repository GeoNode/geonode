/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
function reactCellRendererFactoryParams(ReactComponent, compParams) {
    return function(params) {
        params.eParentOfValue.addElementAttachedListener(function(eCell) {
            ReactDOM.render(<ReactComponent params={params} {...compParams}/>, eCell);
            params.api.addVirtualRowListener('virtualRowRemoved', params.rowIndex, function() {
                ReactDOM.unmountComponentAtNode(eCell);
            });
        });
        // return null to the grid, as we don't want it responsible for rendering
        return null;
    };
}
module.exports = reactCellRendererFactoryParams;
