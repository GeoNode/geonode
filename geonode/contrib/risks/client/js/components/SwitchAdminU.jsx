/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Tooltip, OverlayTrigger} = require('react-bootstrap');

const SwitchAdminU = React.createClass({
    propTypes: {
           toggleAdminUnit: React.PropTypes.func,
           showSubUnit: React.PropTypes.bool,
           show: React.PropTypes.bool
        },
        getDefaultProps() {
           return {
               toggleDim: () => {}
           };
       },
        render() {
            const {toggleAdminUnit, showSubUnit, show} = this.props;
            const icon = showSubUnit ? "stop" : "th";
            const label = showSubUnit ? "Hide Sub-units values" : "Show Sub-units values";
            const tooltip = (<Tooltip id={"tooltip-sub-value"} className="disaster">{label}</Tooltip>);
            return show ? (
                <OverlayTrigger placement="bottom" overlay={tooltip}>
                    <button id="disaster-sub-units-button" className="btn btn-primary" onClick={toggleAdminUnit}>
                        <i className={"fa fa-" + icon}/>
                    </button>
                </OverlayTrigger>
            ) : null;
        }
});

module.exports = SwitchAdminU;
