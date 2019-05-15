/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var Legend = require('./legend/Legend');

var WMSLegend = React.createClass({
    propTypes: {
        node: React.PropTypes.object,
        showOnlyIfVisible: React.PropTypes.bool
    },
    getDefaultProps() {
        return {
            showOnlyIfVisible: false
        };
    },
    render() {
        let node = this.props.node || {};
        if (this.canShow(node) && node.type === "wms" && node.group !== "background") {
            return <div style={{marginLeft: "15px"}}><Legend layer={node}/></div>;
        }
        return null;
    },
    canShow(node) {
        return node.visibility || !this.props.showOnlyIfVisible;
    }
});

module.exports = WMSLegend;
