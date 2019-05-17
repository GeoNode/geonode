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

var MousePositionLabelDM = React.createClass({
    propTypes: {
        position: React.PropTypes.shape({
            lng: React.PropTypes.number,
            lat: React.PropTypes.number
        })
    },
    getPositionValues(mPos) {
        let {lng, lat} = (mPos) ? mPos : [null, null];
        let [latM, lngM] = [(lat % 1) * 60, (lng % 1) * 60];
        return {
            lat,
            latM: Math.abs(latM),
            lng,
            lngM: Math.abs(lngM)
        };
    },
    render() {
        let pos = this.getPositionValues(this.props.position);
        let integerFormat = {style: "decimal", minimumIntegerDigits: 2, maximumFractionDigits: 0};
        let decimalFormat = {style: "decimal", minimumIntegerDigits: 2, maximumFractionDigits: 3, minimumFractionDigits: 3};
        let lngDFormat = {style: "decimal", minimumIntegerDigits: 3, maximumFractionDigits: 0};
        return (
                <h5>
                <Label bsSize="lg" bsStyle="info">
                    <span>Lat: </span><NumberFormat key="latD" numberParams={integerFormat} value={pos.lat} />
                    <span>° </span><NumberFormat key="latM" numberParams={decimalFormat} value={pos.latM} />
                    <span>&apos; </span>
                    <span>Lng: </span><NumberFormat key="lngD" numberParams={lngDFormat} value={pos.lng} />
                    <span>° </span><NumberFormat key="lngM" numberParams={decimalFormat} value={pos.lngM} />
                    <span>&apos; </span>
                </Label>
                </h5>);
    }
});

module.exports = MousePositionLabelDM;
