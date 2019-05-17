/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {FormControl} = require('react-bootstrap');
const LocaleUtils = require('../../../utils/LocaleUtils');

const TextField = React.createClass({
    propTypes: {
        operator: React.PropTypes.string,
        fieldName: React.PropTypes.string,
        fieldRowId: React.PropTypes.number,
        attType: React.PropTypes.string,
        fieldValue: React.PropTypes.string,
        label: React.PropTypes.string,
        fieldException: React.PropTypes.oneOfType([
            React.PropTypes.object,
            React.PropTypes.string
        ]),
        onUpdateField: React.PropTypes.func,
        onUpdateExceptionField: React.PropTypes.func,
        style: React.PropTypes.object
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            operator: "like",
            fieldName: null,
            fieldRowId: null,
            attType: "string",
            fieldValue: null,
            label: null,
            fieldException: null,
            onUpdateField: () => {},
            onUpdateExceptionField: () => {},
            style: {}
        };
    },
    componentDidMount() {
        if (this.props.operator === "isNull" && !this.props.fieldValue) {
            this.props.onUpdateField(this.props.fieldRowId, this.props.fieldName, " ", this.props.attType);
        }
    },
    componentDidUpdate() {
        if (this.props.operator === "isNull" && !this.props.fieldValue) {
            this.props.onUpdateField(this.props.fieldRowId, this.props.fieldName, " ", this.props.attType);
        }
    },
    render() {
        let placeholder = LocaleUtils.getMessageById(this.context.messages, "queryform.attributefilter.text_placeholder");
        let label = this.props.label ? (<label>{this.props.label}</label>) : (<span/>);
        return (
            <div className="textField">
                {label}
                <FormControl
                    disabled={this.props.operator === "isNull"}
                    placeholder={placeholder}
                    onChange={this.changeText}
                    type="text"
                    value={this.props.fieldValue || ''}
                />
            </div>);
    },
    changeText(e) {
        this.props.onUpdateField(this.props.fieldRowId, this.props.fieldName, e.target.value, this.props.attType);
    }
});

module.exports = TextField;
