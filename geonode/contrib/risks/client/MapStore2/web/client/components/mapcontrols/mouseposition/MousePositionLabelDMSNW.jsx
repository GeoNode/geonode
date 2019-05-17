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

var MousePositionLabelDMS = React.createClass({
    propTypes: {
        position: React.PropTypes.shape({
            lng: React.PropTypes.number,
            lat: React.PropTypes.number
        })
    },
    getPositionValues(mPos) {
        let {lng, lat} = (mPos) ? mPos : [null, null];
        let [latM, lngM] = [(lat % 1) * 60, (lng % 1) * 60];
        let [latS, lngS] = [(latM % 1) * 60, (lngM % 1) * 60];
        return {
            lat,
            latM: Math.abs(latM),
            latS: Math.abs(latS),
            lng,
            lngM: Math.abs(lngM),
            lngS: Math.abs(lngS)
        };
    },
    render() {
        let pos = this.getPositionValues(this.props.position);
        let integerFormat = {style: "decimal", minimumIntegerDigits: 2, maximumFractionDigits: 0};
        let decimalFormat = {style: "decimal", minimumIntegerDigits: 2, maximumFractionDigits: 2, minimumFractionDigits: 2};
        let lngDFormat = {style: "decimal", minimumIntegerDigits: 3, maximumFractionDigits: 0};
        return (
                <h5>

                <Label bsSize="lg" bsStyle="info">
                    <NumberFormat key="latD" numberParams={integerFormat} value={Math.abs(pos.lat)} />
                    <span>° </span><NumberFormat key="latM" numberParams={integerFormat} value={pos.latM} />
                    <span>&apos; </span><NumberFormat key="latS" numberParams={decimalFormat} value={pos.latS} />
                    <span>&apos;&apos; {pos.lat > 0 ? "N" : "S"} </span><NumberFormat key="lngD" numberParams={lngDFormat} value={Math.abs(pos.lng)} />
                    <span>° </span><NumberFormat key="lngM" numberParams={integerFormat} value={pos.lngM} />
                    <span>&apos; </span><NumberFormat key="lngS" numberParams={decimalFormat} value={pos.lngS} /><span>'' {pos.lng > 0 ? "E" : "W"}</span>
                </Label>
                </h5>);
    }
});

module.exports = MousePositionLabelDMS;
