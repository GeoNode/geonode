/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Tooltip, OverlayTrigger} = require('react-bootstrap');

const DrillUpBtn = React.createClass({
    propTypes: {
        label: React.PropTypes.string,
        href: React.PropTypes.string,
        geom: React.PropTypes.string,
        zoomOut: React.PropTypes.func,
        disabled: React.PropTypes.bool
    },
    getDefaultProps() {
        return {
            zoomOut: () => {}
        };
    },
    render() {
        const {label, disabled} = this.props;
        const tooltip = (
            <Tooltip id="tooltip-drillup" className="disaster">{`Zoom out to ${label}`}</Tooltip>
        );
        return disabled ? null : (
          <OverlayTrigger className="disaster" placement="bottom" overlay={tooltip}>
            <button className="btn btn-primary" onClick={this.onClick}>
              <i className="icon-zoom-out"/>
            </button>
          </OverlayTrigger>
        );
    },
    onClick() {
        const {href, zoomOut, geom} = this.props;
        zoomOut(href, geom);
    }
});

module.exports = DrillUpBtn;
