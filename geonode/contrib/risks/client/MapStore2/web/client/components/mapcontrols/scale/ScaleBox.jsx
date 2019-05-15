/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {FormControl, FormGroup, ControlLabel} = require('react-bootstrap');
const mapUtils = require('../../../utils/MapUtils');
const {isEqual} = require('lodash');

var ScaleBox = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        style: React.PropTypes.object,
        scales: React.PropTypes.array,
        currentZoomLvl: React.PropTypes.number,
        onChange: React.PropTypes.func,
        readOnly: React.PropTypes.bool,
        label: React.PropTypes.string,
        template: React.PropTypes.func,
        useRawInput: React.PropTypes.bool
    },
    getDefaultProps() {
        return {
            id: 'mapstore-scalebox',
            scales: mapUtils.getGoogleMercatorScales(0, 28),
            currentZoomLvl: 0,
            onChange() {},
            readOnly: false,
            template: (scale) => ("1 : " + Math.round(scale)),
            useRawInput: false
        };
    },
    shouldComponentUpdate(nextProps) {
        return !isEqual(nextProps, this.props);
    },
    onComboChange(event) {
        var selectedZoomLvl = parseInt(event.nativeEvent.target.value, 10);
        this.props.onChange(selectedZoomLvl);
    },
    getOptions() {
        return this.props.scales.map((item, index) => {
            return (
                <option value={index} key={index}>{this.props.template(item, index)}</option>
            );
        });
    },
    render() {
        var control = null;
        if (this.props.readOnly) {
            control = (
                <label>{this.props.template(this.props.scales[this.props.currentZoomLvl], this.props.currentZoomLvl)}</label>
            );
        } else if (this.props.useRawInput) {
            control = (
                <select label={this.props.label} onChange={this.onComboChange} bsSize="small" value={this.props.currentZoomLvl || ""}>
                    {this.getOptions()}
                </select>
            );
        } else {
            control = (
                <FormGroup bsSize="small">
                    <ControlLabel>{this.props.label}</ControlLabel>
                    <FormControl componentClass="select" onChange={this.onComboChange} value={this.props.currentZoomLvl || ""}>
                        {this.getOptions()}
                    </FormControl>
                </FormGroup>
            );
        }
        return (

            <div id={this.props.id} style={this.props.style}>
                {control}
            </div>
        );
    }
});

module.exports = ScaleBox;
