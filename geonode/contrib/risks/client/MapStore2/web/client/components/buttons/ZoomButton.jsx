/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Button, Glyphicon, Tooltip, OverlayTrigger} = require('react-bootstrap');

const ZoomButton = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        style: React.PropTypes.object,
        glyphicon: React.PropTypes.string,
        text: React.PropTypes.string,
        btnSize: React.PropTypes.oneOf(['large', 'small', 'xsmall']),
        className: React.PropTypes.string,
        help: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        step: React.PropTypes.number,
        currentZoom: React.PropTypes.number,
        minZoom: React.PropTypes.number,
        maxZoom: React.PropTypes.number,
        onZoom: React.PropTypes.func,
        tooltip: React.PropTypes.element,
        tooltipPlace: React.PropTypes.string,
        bsStyle: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            id: "mapstore-zoom",
            className: "square-button",
            glyphicon: "plus",
            btnSize: 'xsmall',
            tooltipPlace: "left",
            step: 1,
            currentZoom: 3,
            minZoom: 0,
            maxZoom: 28,
            onZoom: () => {},
            bsStyle: "default"
        };
    },
    render() {
        return this.addTooltip(
            <Button
                id={this.props.id}
                style={this.props.style}
                onClick={() => this.props.onZoom(this.props.currentZoom + this.props.step)}
                className={this.props.className}
                disabled={(this.props.currentZoom + this.props.step > this.props.maxZoom) || (this.props.currentZoom + this.props.step < this.props.minZoom)}
                bsStyle={this.props.bsStyle}
                >
                {this.props.glyphicon ? <Glyphicon glyph={this.props.glyphicon}/> : null}
                {this.props.glyphicon && this.props.text ? "\u00A0" : null}
                {this.props.text}
                {this.props.help}
            </Button>
        );
    },
    addTooltip(btn) {
        if (!this.props.tooltip) {
            return btn;
        }
        let tooltip = <Tooltip id="locate-tooltip">{this.props.tooltip}</Tooltip>;
        return (
            <OverlayTrigger placement={this.props.tooltipPlace} key={"overlay-trigger." + this.props.id} overlay={tooltip}>
                {btn}
            </OverlayTrigger>
        );
    }
});

module.exports = ZoomButton;
