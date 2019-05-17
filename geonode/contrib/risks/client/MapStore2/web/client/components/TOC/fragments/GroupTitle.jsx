/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const StatusIcon = require('./StatusIcon');
require("./css/grouptitle.css");

const GroupTitle = React.createClass({
    propTypes: {
        node: React.PropTypes.object,
        onClick: React.PropTypes.func,
        style: React.PropTypes.object
    },
    statics: {
        inheritedPropTypes: ['node']
    },
    getDefaultProps() {
        return {
            onClick: () => {},
            style: {

            }
        };
    },
    render() {
        let expanded = (this.props.node.expanded !== undefined) ? this.props.node.expanded : true;
        let groupTitle = this.props.node && this.props.node.title || 'Default';
        return (
            <div className="toc-group-title" onClick={() => this.props.onClick(this.props.node.id, expanded)} style={this.props.style}>
                <StatusIcon expanded={expanded} node={this.props.node}/>{groupTitle}
            </div>
        );
    }
});

module.exports = GroupTitle;
