/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var assign = require('object-assign');

var ImageButton = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        image: React.PropTypes.string,
        onClick: React.PropTypes.func,
        style: React.PropTypes.object,
        disabled: React.PropTypes.bool,
        tooltip: React.PropTypes.string,
        className: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            disabled: false,
            tooltip: null,
            className: undefined
        };
    },
    getStyle() {
        var cursorStyle = this.props.disabled ? "not-allowed" : "pointer";
        var finalStyle = {
            cursor: cursorStyle,
            margin: 0,
            padding: 0,
            display: "inline-block"
        };
        if (this.props.image) {
            assign(finalStyle, {
                overflow: "hidden"
            });
        } else {
            assign(finalStyle, {
                height: "48px",
                width: "48px",
                border: "1px solid grey",
                borderRadius: "4px",
                backgroundColor: "rgb(250, 250, 250)"
            });
        }
        assign(finalStyle, this.props.style);
        return finalStyle;
    },
    render() {
        return (
            <img className={this.props.className} id={this.props.id} title={this.props.tooltip} style={this.getStyle()} src={this.props.image}
                onClick={this.props.disabled ? null : this.props.onClick}></img>
        );
    }
});

module.exports = ImageButton;
