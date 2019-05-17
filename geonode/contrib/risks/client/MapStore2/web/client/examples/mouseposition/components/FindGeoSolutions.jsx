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
var ProgressBar = BootstrapReact.ProgressBar;
var ReactIntl = require('react-intl');
var FormattedNumber = ReactIntl.FormattedNumber;

var SearchTarget = React.createClass({
    propTypes: {
        position: React.PropTypes.shape({
            lng: React.PropTypes.number,
            lat: React.PropTypes.number
        }),
        geosolutions: React.PropTypes.shape({
            lng: React.PropTypes.number,
            lat: React.PropTypes.number
        })
    },
    getDefaultProps() {
        return {
            position: null,
            geosolutions: {
                lng: 10.298046,
                lat: 43.883948
            }
        };
    },
    getDistanceToGaol(mPos) {
        // code from http://www.movable-type.co.uk/scripts/latlong.html
        var R = 6371; // kmetres
        var φ1 = this.props.geosolutions.lat * Math.PI / 180;
        var φ2 = mPos.lat * Math.PI / 180;
        var Δφ = (mPos.lat - this.props.geosolutions.lat) * Math.PI / 180;
        var Δλ = (mPos.lng - this.props.geosolutions.lng) * Math.PI / 180;
        var a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) + Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
        var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        var d = R * c;
        return d;
    },
    render() {
        let d = this.getDistanceToGaol(this.props.position);
        let integerFormat = {style: "decimal", minimumFractionDigits: 3, maximumFractionDigits: 3};
        return (
                <h5>
                <Label bsSize="lg" bsStyle="info">
                    {d < 0.1 ?
                        <div id="geoslable">
                        <span className="font-effect-shadow-multiple">GeoSolutions</span></div> :
                        <div>
                            <span>Move your mouse to find the target.<br/>Distance: </span>
                            <FormattedNumber key="distance" {...integerFormat} value={d} bsSize="lg"/>
                            <span> Km</span>
                            <ProgressBar active now={d * 10} />
                        </div>
                    }
                </Label>
                </h5>);
    }
});

module.exports = SearchTarget;
