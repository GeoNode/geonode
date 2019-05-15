/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const assign = require('object-assign');

const {OverlayTrigger, Tooltip} = require('react-bootstrap');

const {DropdownList, Multiselect} = require('react-widgets');

const LocaleUtils = require('../../../utils/LocaleUtils');

const ComboField = React.createClass({
    propTypes: {
        busy: React.PropTypes.bool,
        style: React.PropTypes.object,
        valueField: React.PropTypes.string,
        textField: React.PropTypes.string,
        fieldOptions: React.PropTypes.array,
        fieldName: React.PropTypes.string,
        fieldRowId: React.PropTypes.number,
        attType: React.PropTypes.string,
        fieldValue: React.PropTypes.oneOfType([
            React.PropTypes.number,
            React.PropTypes.string,
            React.PropTypes.array
        ]),
        fieldException: React.PropTypes.oneOfType([
            React.PropTypes.object,
            React.PropTypes.string
        ]),
        comboFilter: React.PropTypes.oneOfType([
            React.PropTypes.bool,
            React.PropTypes.string,
            React.PropTypes.func
        ]),
        groupBy: React.PropTypes.oneOfType([
            React.PropTypes.string,
            React.PropTypes.func
        ]),
        multivalue: React.PropTypes.bool,
        disabled: React.PropTypes.bool,
        options: React.PropTypes.object,
        onSelect: React.PropTypes.func,
        onToggle: React.PropTypes.func,
        onSearch: React.PropTypes.func,
        onUpdateField: React.PropTypes.func,
        onClick: React.PropTypes.func,
        onUpdateExceptionField: React.PropTypes.func
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            options: {},
            busy: false,
            style: {
                width: "100%"
            },
            multivalue: false,
            disabled: false,
            valueField: null,
            textField: null,
            fieldOptions: [],
            fieldName: null,
            fieldRowId: null,
            fieldValue: null,
            fieldException: null,
            comboFilter: false,
            groupBy: () => {},
            onSelect: () => {},
            onToggle: () => {},
            onSearch: () => {},
            onUpdateField: () => {},
            onUpdateExceptionField: () => {}
        };
    },
    render() {
        let style = assign({}, {borderColor: "#dedede"}, this.props.style);

        if (this.props.fieldException) {
            style = assign({}, style, {borderColor: "#FF0000"});
        }

        let placeholder = LocaleUtils.getMessageById(this.context.messages, "queryform.attributefilter.combo_placeholder");

        const ListComponent = this.props.multivalue ? Multiselect : DropdownList;

        const list = this.props.valueField !== null && this.props.textField !== null ? (
            <ListComponent
                {...this.props.options}
                busy={this.props.busy}
                disabled={this.props.disabled}
                valueField={this.props.valueField}
                textField={this.props.textField}
                data={this.props.fieldOptions}
                value={this.props.fieldValue}
                caseSensitive={false}
                minLength={3}
                placeholder={placeholder}
                filter={this.props.comboFilter}
                style={style}
                groupBy={this.props.groupBy}
                onSelect={this.props.onSelect}
                onChange={(value) => this.props.onUpdateField(this.props.fieldRowId, this.props.fieldName, this.props.multivalue ? value : value[this.props.valueField], this.props.attType)}
                onToggle={this.props.onToggle}
                onSearch={this.props.onSearch}/>
        ) : (
            <ListComponent
                {...this.props.options}
                busy={this.props.busy}
                disabled={this.props.disabled}
                data={this.props.fieldOptions}
                value={this.props.fieldValue}
                caseSensitive={false}
                minLength={3}
                placeholder={placeholder}
                filter={this.props.comboFilter}
                style={style}
                groupBy={this.props.groupBy}
                onSelect={this.props.onSelect}
                onChange={(value) => this.props.onUpdateField(this.props.fieldRowId, this.props.fieldName, value, this.props.attType)}
                onToggle={this.props.onToggle}
                onSearch={this.props.onSearch}/>
        );

        return this.props.fieldException ? (
            <OverlayTrigger placement="bottom" overlay={(
                    <Tooltip id={this.props.fieldRowId + "_tooltip"}>
                        <strong>
                            {this.props.fieldException}
                        </strong>
                    </Tooltip>
            )}>
                {list}
            </OverlayTrigger>
        ) : (
            list
        );
    }
});

module.exports = ComboField;
