/**
 * Copyright 2015-2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var {Button, Glyphicon, OverlayTrigger, Tooltip} = require('react-bootstrap');
const defaultIcon = require('../../misc/spinners/InlineSpinner/img/spinner.gif');
require('./css/locate.css');
let checkingGeoLocation = false;
let geoLocationAllowed = false;

const LocateBtn = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        btnConfig: React.PropTypes.object,
        text: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        help: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        locate: React.PropTypes.string,
        onClick: React.PropTypes.func,
        tooltip: React.PropTypes.element,
        tooltipPlace: React.PropTypes.string,
        style: React.PropTypes.object,
        bsStyle: React.PropTypes.string,
        glyph: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            id: "locate-btn",
            onClick: () => {},
            locate: "DISABLED",
            tooltipPlace: "left",
            bsStyle: "default",
            glyph: "1-position-1",
            btnConfig: {
                className: "square-button"
            }
        };
    },
    onClick() {
        let status;
        switch (this.props.locate) {
            case "FOLLOWING":
                status = "DISABLED";
                break;
            case "ENABLED":
                status = "FOLLOWING";
                break;
            case "DISABLED":
                status = "ENABLED";
                break;
            case "LOCATING":
                status = "DISABLED";
                break;
            case "PERMISSION_DENIED":
                status = "DISABLED";
                break;
            default:
                break;
        }
        this.props.onClick(status);
    },
    renderButton() {
        const geoLocationDisabled = this.props.locate === "PERMISSION_DENIED";
        return (
            <Button id={this.props.id} disabled={geoLocationDisabled} {...this.props.btnConfig} onClick={this.onClick} bsStyle={this.getBtnStyle()} style={this.props.style}>
                <Glyphicon glyph={this.props.glyph}/>{this.props.text}{this.props.help}
            </Button>
        );
    },
    renderLoadingButton() {
        let img = (
            <img src={defaultIcon} style={{
                display: 'inline-block',
                margin: '0px',
                padding: 0,
                background: 'transparent',
                border: 0
            }} alt="..." />
        );
        return (
            <Button id={this.props.id} onClick={this.onClick} {...this.props.btnConfig} bsStyle={this.getBtnStyle()} style={this.props.style}>
                {img}
            </Button>
        );
    },
    addTooltip(btn) {
        let tooltip = <Tooltip id="locate-tooltip">{this.props.tooltip}</Tooltip>;
        return (
            <OverlayTrigger placement={this.props.tooltipPlace} key={"overlay-trigger." + this.props.id} overlay={tooltip}>
                {btn}
            </OverlayTrigger>
        );
    },
    componentWillMount() {
        if (this.props.locate !== 'PERMISSION_DENIED' && !checkingGeoLocation && !geoLocationAllowed) {
            // check if we are allowed to use geolocation feature
            checkingGeoLocation = true;
            navigator.geolocation.getCurrentPosition(() => {
                checkingGeoLocation = false;
                geoLocationAllowed = true;
            }, (error) => {
                checkingGeoLocation = false;
                if (error.code === 1) {
                    this.props.onClick("PERMISSION_DENIED");
                }
            });
        }
    },
    render() {
        var retval;
        var btn = (this.props.locate === "LOCATING") ? this.renderLoadingButton() : this.renderButton();
        if (this.props.tooltip) {
            retval = this.addTooltip(btn);
        } else {
            retval = btn;
        }
        return retval;

    },
    getBtnStyle() {
        let style = this.props.bsStyle;
        if (this.props.locate === "FOLLOWING") {
            style = "success";
        }else if (this.props.locate === "ENABLED") {
            style = "info";
        }
        return style;
    }
});

module.exports = LocateBtn;
