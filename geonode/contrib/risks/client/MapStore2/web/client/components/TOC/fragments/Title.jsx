/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
require("./css/toctitle.css");
const Title = React.createClass({
    propTypes: {
        node: React.PropTypes.object,
        onClick: React.PropTypes.func
    },
    statics: {
        inheritedPropTypes: ['node']
    },
    getDefaultProps() {
        return {
            onClick: () => {}
        };
    },
    render() {
        let expanded = (this.props.node.expanded !== undefined) ? this.props.node.expanded : true;
        return (<span className="toc-title" onClick={() => this.props.onClick(this.props.node.id || this.props.node.name, expanded)}>{this.props.node.title || this.props.node.name}</span>);
    }
});

module.exports = Title;
