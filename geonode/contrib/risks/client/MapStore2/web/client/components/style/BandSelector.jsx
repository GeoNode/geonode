/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');

const {Grid, Row, Col} = require('react-bootstrap');

const Combobox = require('react-widgets').Combobox;
const numberLocalizer = require('react-widgets/lib/localizers/simple-number');
numberLocalizer();
const {NumberPicker} = require('react-widgets');
require('react-widgets/lib/less/react-widgets.less');

const Message = require('../I18N/Message');
const LocaleUtils = require('../../utils/LocaleUtils');

const BandSelector = React.createClass({
    propTypes: {
        band: React.PropTypes.oneOfType([React.PropTypes.number, React.PropTypes.string]),
        bands: React.PropTypes.array,
        min: React.PropTypes.number,
        max: React.PropTypes.number,
        contrast: React.PropTypes.oneOf(['none', 'Normalize', 'Histogram', 'GammaValue']),
        algorithm: React.PropTypes.oneOf(['none', 'StretchToMinimumMaximum', 'ClipToMinimumMaximum', 'ClipToZero']),
        gammaValue: React.PropTypes.number,
        onChange: React.PropTypes.func,
        bandsComboOptions: React.PropTypes.object
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            band: '1',
            contrast: "none",
            algorithm: "none",
            gammaValue: 1,
            min: 0,
            max: 255,
            bandsComboOptions: {},
            onChange: () => {},
            bands: ['1', '2', '3']
        };
    },
    render() {
        return (
                <Grid fluid>
                    <Row>
                        <Col xs={4}><label><Message msgId="bandselector.band"/></label> </Col>
                        <Col xs={4}><label><Message msgId="bandselector.enhancement"/></label></Col>
                        {this.props.contrast === "GammaValue" ? (<Col xs={4}> <label><Message msgId="bandselector.value"/></label> </Col>) : null }
                        {this.props.contrast === "Normalize" ? (<Col xs={4}><label><Message msgId="bandselector.algorithmTitle"/></label></Col>) : null }
                    </Row>
                    <Row>
                        <Col xs={4}>
                            <Combobox
                                data={this.props.bands}
                                value={this.props.band}
                                onChange={(v) => this.props.onChange("band", v)}
                                {...this.props.bandsComboOptions}/>
                        </Col>
                        <Col xs={4}>
                            <Combobox data={[
                            {value: "none", name: LocaleUtils.getMessageById(this.context.messages, "bandselector.enha.none")},
                            {value: 'Normalize', name: LocaleUtils.getMessageById(this.context.messages, "bandselector.enha.Normalize")},
                            {value: 'Histogram', name: LocaleUtils.getMessageById(this.context.messages, "bandselector.enha.Histogram")},
                            {value: 'GammaValue', 'name': LocaleUtils.getMessageById(this.context.messages, "bandselector.enha.GammaValue")}]}
                            valueField="value"
                            textField="name"
                            value={this.props.contrast}
                            onChange={(v) => this.props.onChange("contrast", v.value)}/>
                        </Col>
                        { this.props.contrast === "GammaValue" ? (<Col xs={4}>
                            <NumberPicker
                                format="-#,###.##"
                                precision={3}
                                step={0.1}
                                min={0}
                                value={this.props.gammaValue}
                                onChange={(v) => this.props.onChange("gammaValue", v)}/></Col>) : null}
                        { this.props.contrast === "Normalize" ? (
                             <Col xs={4}>
                            <Combobox data={[
                            {value: "none", name: LocaleUtils.getMessageById(this.context.messages, "bandselector.algorithm.none")},
                            {value: 'StretchToMinimumMaximum', name: LocaleUtils.getMessageById(this.context.messages, "bandselector.algorithm.StretchToMinimumMaximum")},
                            {value: 'ClipToMinimumMaximum', name: LocaleUtils.getMessageById(this.context.messages, "bandselector.algorithm.ClipToMinimumMaximum")},
                            {value: 'ClipToZero', 'name': LocaleUtils.getMessageById(this.context.messages, "bandselector.algorithm.ClipToZero")}]}
                            valueField="value"
                            textField="name"
                            value={this.props.algorithm}
                            onChange={(v) => this.props.onChange("algorithm", v.value)}/>
                        </Col>
                            ) : null}
                    </Row>
                        {this.props.contrast === "Normalize" && this.props.algorithm !== "none" ? (
                    <Row>
                        <Col xsOffset={2} xs={4}><label><Message msgId="bandselector.min"/></label></Col>
                        <Col xs={4}><label><Message msgId="bandselector.max"/></label></Col>
                    </Row>) : null }
                    {this.props.contrast === "Normalize" && this.props.algorithm !== "none" ? (
                    <Row>
                        <Col xsOffset={2} xs={4}>
                        <NumberPicker
                            format="-#,###.##"
                            precision={3}
                            max={this.props.max - 1}
                            value={this.props.min}
                            onChange={(v) => this.props.onChange("min", v)}
                        /></Col>
                        <Col xs={4}>
                        <NumberPicker
                            format="-#,###.##"
                            precision={3}
                            min={this.props.min + 1}
                            value={this.props.max}
                            onChange={(v) => this.props.onChange("max", v)}
                        /></Col>
                    </Row>) : null }
                </Grid>);
    }
});

module.exports = BandSelector;
