/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var {Button, Glyphicon, OverlayTrigger} = require('react-bootstrap');
var ImageButton = require('./ImageButton');

var ToggleButton = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        btnConfig: React.PropTypes.object,
        text: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        help: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        glyphicon: React.PropTypes.string,
        pressed: React.PropTypes.bool,
        onClick: React.PropTypes.func,
        tooltip: React.PropTypes.element,
        tooltipPlace: React.PropTypes.string,
        style: React.PropTypes.object,
        btnType: React.PropTypes.oneOf(['normal', 'image']),
        image: React.PropTypes.string,
        pressedStyle: React.PropTypes.string,
        defaultStyle: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            onClick: () => {},
            pressed: false,
            tooltipPlace: "top",
            style: {width: "100%"},
            btnType: 'normal',
            pressedStyle: 'primary',
            defaultStyle: 'default'
        };
    },
    onClick() {
        this.props.onClick(!this.props.pressed);
    },
    renderNormalButton() {
        return (
            <Button id={this.props.id} {...this.props.btnConfig} onClick={this.onClick} bsStyle={this.props.pressed ? this.props.pressedStyle : this.props.defaultStyle} style={this.props.style}>
                {this.props.glyphicon ? <Glyphicon glyph={this.props.glyphicon}/> : null}
                {this.props.glyphicon && this.props.text && !React.isValidElement(this.props.text) ? "\u00A0" : null}
                {this.props.text}
                {this.props.help}
            </Button>
        );
    },
    renderImageButton() {
        return (
            <ImageButton id={this.props.id} image={this.props.image} onClick={this.onClick} style={this.props.style}/>
        );
    },
    addTooltip(btn) {
        return (
            <OverlayTrigger placement={this.props.tooltipPlace} key={"overlay-trigger." + this.props.id} overlay={this.props.tooltip}>
                {btn}
            </OverlayTrigger>
        );
    },
    render() {
        var retval;
        var btn = this.props.btnType === 'normal' ? this.renderNormalButton() : this.renderImageButton();
        if (this.props.tooltip) {
            retval = this.addTooltip(btn);
        } else {
            retval = btn;
        }
        return retval;

    }
});

module.exports = ToggleButton;
