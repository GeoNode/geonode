/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Tooltip, OverlayTrigger, Row, Col} = require("react-bootstrap");
const LocaleUtils = require('../../../utils/LocaleUtils');
const numberLocalizer = require('react-widgets/lib/localizers/simple-number');
numberLocalizer();
const {NumberPicker} = require('react-widgets');

const NumberField = React.createClass({
    propTypes: {
        operator: React.PropTypes.string,
        fieldName: React.PropTypes.string,
        fieldRowId: React.PropTypes.number,
        attType: React.PropTypes.string,
        fieldValue: React.PropTypes.oneOfType([
            React.PropTypes.number,
            React.PropTypes.object]),
        fieldException: React.PropTypes.oneOfType([
            React.PropTypes.object,
            React.PropTypes.bool,
            React.PropTypes.string
        ]),
        onUpdateField: React.PropTypes.func,
        onUpdateExceptionField: React.PropTypes.func,
        isRequired: React.PropTypes.bool,
        label: React.PropTypes.string,
        lowLabel: React.PropTypes.string,
        upLabel: React.PropTypes.string,
        options: React.PropTypes.shape({
            format: React.PropTypes.string,
            min: React.PropTypes.number,
            max: React.PropTypes.number,
            step: React.PropTypes.number,
            precision: React.PropTypes.number
        }),
        style: React.PropTypes.object
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            style: { borderColor: "#dedede"},
            operator: "=",
            fieldName: null,
            fieldRowId: null,
            attType: "number",
            fieldValue: null,
            fieldException: null,
            isRequired: false,
            label: null,
            lowLabel: null,
            upLabel: null,
            options: {},
            onUpdateField: () => {},
            onUpdateExceptionField: () => {}
        };
    },
    renderPicker(style) {
        let label = this.props.label ? (<label>{this.props.label}</label>) : null;
        let lowLabel = this.props.lowLabel ? (<label>{this.props.lowLabel}</label>) : null;
        let upLabel = this.props.upLabel ? (<label>{this.props.upLabel}</label>) : null;
        return this.props.operator === "><" ? (
                <div>
                    <Row>
                        <Col xs={6}>
                            {lowLabel}
                            <NumberPicker
                                style={style}
                                value={this.props.fieldValue && (this.props.fieldValue.lowBound !== null && this.props.fieldValue.lowBound !== undefined) ? this.props.fieldValue.lowBound : null}
                                onChange={(value) => this.changeNumber({lowBound: value, upBound: this.props.fieldValue && (this.props.fieldValue.upBound !== null && this.props.fieldValue.upBound !== undefined ) ? this.props.fieldValue.upBound : null})}
                                {...this.props.options}
                            />
                        </Col>
                        <Col xs={6}>
                            {upLabel}
                            <NumberPicker
                                style={style}
                                value={this.props.fieldValue && (this.props.fieldValue.upBound !== null && this.props.fieldValue.upBound !== undefined ) ? this.props.fieldValue.upBound : null}
                                onChange={(value) => this.changeNumber({upBound: value, lowBound: this.props.fieldValue && (this.props.fieldValue.lowBound !== null && this.props.fieldValue.lowBound !== undefined) ? this.props.fieldValue.lowBound : null})}
                                {...this.props.options}
                            />
                        </Col>
                    </Row>
                </div>
            ) : (
                <Row>
                    <Col xs={12}>
                        {label}
                        <NumberPicker
                        style={style}
                        value={this.props.fieldValue && (this.props.fieldValue.lowBound !== null && this.props.fieldValue.lowBound !== undefined) ? this.props.fieldValue.lowBound : this.props.fieldValue}
                        onChange={this.changeNumber}
                        {...this.props.options}
                        />
                    </Col>
                </Row>
            );
    },
    render() {
        let style = this.props.style;
        if (this.props.fieldException) {
            style = {...this.props.style, borderColor: "#FF0000"};
        }
        return (
            <OverlayTrigger placement="bottom"
             overlay={(this.props.fieldException) ? (
                    <Tooltip id={this.props.fieldRowId + "_tooltip"}>
                        <strong>
                            {this.props.fieldException}
                        </strong>
                    </Tooltip>
            ) : (<noscript/>)}>
            {this.renderPicker(style)}
            </OverlayTrigger>
            );
    },
    changeNumber(value) {
        if (this.props.operator === "><") {
            if ((value.lowBound !== null && value.lowBound !== undefined) && ( value.upBound !== null && value.upBound !== undefined) && value.lowBound >= value.upBound) {
                this.props.onUpdateExceptionField(this.props.fieldRowId, LocaleUtils.getMessageById(this.context.messages, "queryform.attributefilter.numberfield.wrong_range"));
            }else if (this.props.fieldException) {
                this.props.onUpdateExceptionField(this.props.fieldRowId, null);
            }
        } else {
            if (this.props.isRequired && ( value === null || value === undefined)) {
                this.props.onUpdateExceptionField(this.props.fieldRowId, LocaleUtils.getMessageById(this.context.messages, "queryform.attributefilter.numberfield.isRequired"));
            } else if (this.props.fieldException) {
                this.props.onUpdateExceptionField(this.props.fieldRowId, null);
            }
        }
        this.props.onUpdateField(this.props.fieldRowId, this.props.fieldName, value, this.props.attType);
    }
});

module.exports = NumberField;
