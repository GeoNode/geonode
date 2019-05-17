/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var {Button, Glyphicon, OverlayTrigger, Tooltip} = require('react-bootstrap');

var UndoBtn = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        btnConfig: React.PropTypes.object,
        text: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        help: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        onClick: React.PropTypes.func,
        tooltip: React.PropTypes.element,
        tooltipPlace: React.PropTypes.string,
        style: React.PropTypes.object,
        glyph: React.PropTypes.string,
        buttonStyle: React.PropTypes.string,
        disabled: React.PropTypes.bool
    },
    getDefaultProps() {
        return {
            id: "undo-btn",
            onClick: () => {},
            tooltipPlace: "left",
            glyph: "1-screen-backward",
            buttonStyle: "primary",
            btnConfig: {
                className: "square-button"
            }
        };
    },
    onClick() {
        this.props.onClick();
    },
    shouldComponentUpdate(nextProps) {
        return this.props.disabled !== nextProps.disabled;
    },
    renderButton() {
        return (
            <Button id={this.props.id} disabled={this.props.disabled} {...this.props.btnConfig} onClick={this.onClick} bsStyle={this.props.buttonStyle} style={this.props.style}>
                <Glyphicon glyph={this.props.glyph}/>{this.props.text}{this.props.help}
            </Button>
        );
    },
    addTooltip(btn) {
        let tooltip = <Tooltip id="undo-btn-tooltip">{this.props.tooltip}</Tooltip>;
        return (
            <OverlayTrigger placement={this.props.tooltipPlace} key={"overlay-trigger." + this.props.id} overlay={tooltip}>
                {btn}
            </OverlayTrigger>
        );
    },
    componentWillMount() {
        // none
    },
    render() {
        var retval;
        var btn = this.renderButton();
        if (this.props.tooltip) {
            retval = this.addTooltip(btn);
        } else {
            retval = btn;
        }
        return retval;

    }
});

module.exports = UndoBtn;
