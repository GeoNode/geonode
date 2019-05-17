/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {connect} = require('react-redux');

const Message = require('./locale/Message');

const {changeMeasurement} = require('../actions/measurement');

const MeasureRes = require('../components/mapcontrols/measure/MeasureResults');

const MeasureComponent = React.createClass({
    render() {
        const labels = {
            lengthLabel: <Message msgId="measureComponent.lengthLabel"/>,
            areaLabel: <Message msgId="measureComponent.areaLabel"/>,
            bearingLabel: <Message msgId="measureComponent.bearingLabel"/>
        };
        return <MeasureRes {...labels} {...this.props}/>;
    }
});

const MeasureResultsPlugin = connect((state) => {
    return {
        measurement: state.measurement || {},
        lineMeasureEnabled: state.measurement && state.measurement.lineMeasureEnabled || false,
        areaMeasureEnabled: state.measurement && state.measurement.areaMeasureEnabled || false,
        bearingMeasureEnabled: state.measurement && state.measurement.bearingMeasureEnabled || false
    };
}, {
    toggleMeasure: changeMeasurement
})(MeasureComponent);

module.exports = {
    MeasureResultsPlugin,
    reducers: {measurement: require('../reducers/measurement')}
};
