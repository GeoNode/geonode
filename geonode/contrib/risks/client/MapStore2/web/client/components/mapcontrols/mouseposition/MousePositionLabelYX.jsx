/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var BootstrapReact = require('react-bootstrap');
var Label = BootstrapReact.Label;
var NumberFormat = require('../../I18N/Number');

var MousePositionLabelYX = React.createClass({
    propTypes: {
        position: React.PropTypes.shape({
            x: React.PropTypes.number,
            y: React.PropTypes.number
        })
    },
    render() {
        let format = {style: "decimal", minimumIntegerDigits: 2, maximumFractionDigits: 2, minimumFractionDigits: 2};
        return (
             <h5>
                <Label bsSize="lg" bsStyle="info">
                    <span>X: </span><NumberFormat key="x" numberParams={format} value={this.props.position.x} />
                    <span className="mouseposition-separator"/>
                    <span> Y: </span><NumberFormat key="y" numberParams={format} value={this.props.position.y} />
                </Label>
            </h5>);
    }
});
module.exports = MousePositionLabelYX;
