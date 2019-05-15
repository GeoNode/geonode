/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {Glyphicon} = require('react-bootstrap');

const SettingsPanel = React.createClass({
    propTypes: {
        isPanel: React.PropTypes.bool,
        buttonTooltip: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        style: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            isPanel: true,
            icon: <Glyphicon glyph="cog"/>,
            style: {
                width: "300px"
            }
        };
    },
    render() {
        return (<div style={this.props.style}>
            {this.props.children}
        </div>);

    }
});
module.exports = SettingsPanel;
