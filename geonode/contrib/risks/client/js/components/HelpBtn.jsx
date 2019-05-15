/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Tooltip, OverlayTrigger} = require('react-bootstrap');

const HelpBtn = React.createClass({
    propTypes: {
        label: React.PropTypes.string,
        toggleTutorial: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            label: "Show tutorial",
            toggleTutorial: () => {}
        };
    },
    render() {
        const {label} = this.props;
        const tooltip = (<Tooltip id={"tooltip-sub-value"} className="disaster">{label}</Tooltip>);
        return (
          <OverlayTrigger placement="bottom" overlay={tooltip}>
            <button id="disaster-show-tutorial" className="btn btn-primary" onClick={this.props.toggleTutorial}><i className="fa fa-question"/></button>
          </OverlayTrigger>);
    }
});

module.exports = HelpBtn;
