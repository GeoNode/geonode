/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Tooltip, OverlayTrigger} = require('react-bootstrap');

const SwitchChartBtn = React.createClass({
    propTypes: {
        onToggle: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            onToggle: () => {}
        };
    },
    render() {
        const tooltip = (<Tooltip id={"tooltip-sub-value"} className="disaster">{'Switch chart'}</Tooltip>);
        return (
            <OverlayTrigger placement="bottom" overlay={tooltip}>
                <button id="disaster-switch-chart-button" className="btn btn-primary" onClick={this.props.onToggle}>
                    <i className="fa fa-line-chart"/>
                </button>
            </OverlayTrigger>
        );
    }
});

module.exports = SwitchChartBtn;
