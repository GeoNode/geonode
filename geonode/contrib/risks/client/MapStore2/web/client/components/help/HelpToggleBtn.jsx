/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */


var React = require('react');
var ToggleButton = require('../buttons/ToggleButton');
require("./help.css");

/**
 * A toggle button class for enabling / disabling help modus
 */
let HelpToggleBtn = React.createClass({
    propTypes: {
        key: React.PropTypes.string,
        isButton: React.PropTypes.bool,
        glyphicon: React.PropTypes.string,
        pressed: React.PropTypes.bool,
        changeHelpState: React.PropTypes.func,
        changeHelpwinVisibility: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            key: 'helpButton',
            isButton: true,
            glyphicon: 'question-sign'
        };
    },
    onClick: function() {
        this.props.changeHelpState(!this.props.pressed);
        this.props.changeHelpwinVisibility(false);
    },
    render: function() {
        return (
            <ToggleButton
                key={this.props.key}
                isButton={this.props.isButton}
                glyphicon={this.props.glyphicon}
                pressed={this.props.pressed}
                onClick={this.onClick}/>
        );
    }
});

module.exports = HelpToggleBtn;
