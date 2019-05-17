/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Tooltip, OverlayTrigger} = require('react-bootstrap');

const SwitchDim = React.createClass({
    propTypes: {
        toggleDim: React.PropTypes.func,
        dimName: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            toggleDim: () => {}
        };
    },
    render() {
        const tooltip = (
            <Tooltip id="tooltip-switch" className="disaster">{`Switch to ${this.props.dimName}`}</Tooltip>
          );
        return this.props.dimName ? (
            <OverlayTrigger className="disaster" placement="bottom" overlay={tooltip}>
              <button id="disaster-switch-button" className="btn btn-primary" onClick={this.props.toggleDim}><i className="fa fa-exchange"/>
            </button></OverlayTrigger>) : null;
    }
});

module.exports = SwitchDim;
