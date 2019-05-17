/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var {Glyphicon} = require('react-bootstrap');

var StatusIcon = React.createClass({
    propTypes: {
        node: React.PropTypes.object,
        onClick: React.PropTypes.func
    },
    statics: {
        inheritedPropTypes: ['node', 'expanded']
    },
    getDefaultProps() {
        return {
            node: null,
            onClick: () => {}
        };
    },
    render() {
        let expanded = (this.props.node.expanded !== undefined) ? this.props.node.expanded : true;
        return (
            <Glyphicon style={{marginRight: "8px"}} glyph={expanded ? "folder-open" : "folder-close"} />
        );
    }
});

module.exports = StatusIcon;
