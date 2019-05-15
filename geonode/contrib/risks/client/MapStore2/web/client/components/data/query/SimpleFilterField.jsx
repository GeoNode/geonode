/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Panel, ButtonToolbar, Button, OverlayTrigger, Tooltip} = require('react-bootstrap');
const ComboField = require('./ComboField');
const NumberField = require('./NumberField');
const TextField = require('./TextField');
const {isEqual, head, findIndex} = require('lodash');

const SimpleFilterField = React.createClass({
    propTypes: {
        operator: React.PropTypes.string.isRequired,
        maxLabelSize: React.PropTypes.number,
        label: React.PropTypes.string,
        attribute: React.PropTypes.string.isRequired,
        optionsValues: React.PropTypes.array,
        defaultOptions: React.PropTypes.array,
        optionsLabels: React.PropTypes.object,
        values: React.PropTypes.oneOfType([React.PropTypes.array, React.PropTypes.object, React.PropTypes.number, React.PropTypes.string]),
        multivalue: React.PropTypes.bool,
        combo: React.PropTypes.bool,
        toolbar: React.PropTypes.bool,
        type: React.PropTypes.oneOf(['list', 'number', 'string']).isRequired,
        collapsible: React.PropTypes.bool,
        defaultExpanded: React.PropTypes.bool,
        eventKey: React.PropTypes.string,
        fieldId: React.PropTypes.oneOfType([React.PropTypes.number, React.PropTypes.string]),
        checkboxStyle: React.PropTypes.object,
        radioStyle: React.PropTypes.object,
        comboStyle: React.PropTypes.object,
        sort: React.PropTypes.oneOf(['ASC', 'DESC', false]),
        exception: React.PropTypes.oneOfType([
            React.PropTypes.object,
            React.PropTypes.bool,
            React.PropTypes.string
        ]),
        required: React.PropTypes.bool,
        addAllOpt: React.PropTypes.bool,
        updateFilter: React.PropTypes.func,
        valueFormatter: React.PropTypes.func,
        options: React.PropTypes.object
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            options: null,
            operator: null,
            maxLabelSize: 20,
            sort: false,
            required: false,
            exception: false,
            checkboxStyle: {},
            radioStyle: {},
            comboStyle: {},
            optionsValues: [],
            optionsLabels: {},
            defaultOptions: [],
            values: [],
            attribute: "",
            multivalue: false,
            combo: false,
            toolbar: false,
            type: null,
            collapsible: false,
            defaultExpanded: false,
            updateFilter: () => {},
            valueFormatter: (value, labels) => {
                return (labels[value]) ? labels[value] : value;
            }
        };
    },
    shouldComponentUpdate(nextProps) {
        return !isEqual(this.props, nextProps);
    },
    onRChange(e) {
        this.props.updateFilter(this.props.fieldId, {values: [e.target.value]});
    },
    onCheckChange(e) {
        let values;
        if (e.target.checked) {
            values = [...this.props.values, e.target.value];
        }else {
            values = this.props.values.filter((v) => {
                return v !== e.target.value;
            });
        }
        let exception = (this.props.required && values.length === 0) ? true : false;
        this.props.updateFilter(this.props.fieldId, {values: values, exception: exception});
    },
    onComboChange(id, fieldName, value ) {
        let values = (Array.isArray(value)) ? value : [value];
        let exception = (this.props.required && values.length === 0) ? true : false;
        this.props.updateFilter(id, {values: values, exception: exception});
    },
    onNumberChange(id, fieldName, value) {
        this.props.updateFilter(id, {values: value});
    },
    onNumberException(id, exception) {
        this.props.updateFilter(id, {exception: exception});
    },
    onTextChange(id, fieldName, value) {
        let exception = (this.props.required && value.length === 0) ? true : false;
        this.props.updateFilter(id, {values: value, exception: exception});
    },
    getOptionsValue() {
        let optionsValues = this.props.optionsValues.map((opt) => {
            let val = opt;
            if (val === null) {
                val = "null";
            }else if (typeof val !== 'string') {
                val = opt.toString();
            }
            return val;
        }, this);
        if ( this.props.defaultOptions.length > 0) {
            optionsValues = this.props.defaultOptions.reduce((opts, opt) => {
                let nOpt = head(optionsValues.filter((v) => {
                    return v === opt;
                }));
                if (nOpt) {
                    opts.push(nOpt);
                }
                return opts;
            }, []);
        } else if (this.props.sort) {
            optionsValues = (this.props.sort === "ASC") ? optionsValues.sort() : optionsValues.sort().reverse();
        }
        return optionsValues;
    },
    renderLabel(opt) {
        let lab = this.props.valueFormatter(opt, this.props.optionsLabels, this.props.maxLabelSize);
        return (opt.length > this.props.maxLabelSize) ? (
            <OverlayTrigger placement="right" overlay={(<Tooltip id="lab"><strong>{lab}</strong></Tooltip>)}>
                <span>{lab.slice(0, this.props.maxLabelSize - 4).trim() + "...."}</span>
            </OverlayTrigger>
            )
            : (<span>{lab}</span>);
    },
    renderRadioElements() {
        let optionsValues = this.getOptionsValue();
        return optionsValues.map((opt, idx) => {
            return (
                <label key={idx}
                    style={{marginLeft: "0px", marginRight: "10px", ...this.props.radioStyle}}
                    className="radio-inline">
                    <input
                        onChange={this.onRChange}
                        type="radio"
                        value={opt}
                        name={this.props.attribute}
                        checked={findIndex(this.props.values, (val) => { return val === opt; }) !== -1}/>
                        {this.renderLabel(opt)}
                </label>);
        }, this);
    },
    renderRadioPanel() {
        return this.renderRadioElements();
    },
    renderCheckboxElements() {
        let optionsValues = this.getOptionsValue();
        return optionsValues.map((opt, idx) => {
            return (
                <label
                    key={idx}
                    style={{marginLeft: "0px", marginRight: "10px", width: 100, ...this.props.checkboxStyle}}
                    className="checkbox-inline">
                        <input
                            value={opt}
                            type="checkbox"
                            onChange={this.onCheckChange}
                            checked={findIndex(this.props.values, (val) => { return val === opt; }) !== -1}/>
                        {this.renderLabel(opt)}
                </label>
                );
        }, this);
    },
    renderToolbar() {
        return (
        <ButtonToolbar style={{ marginTop: 10}}>
            <Button style={{marginTop: 5}} bsSize="small" onClick={this.selectAll}>Select All</Button>
            <Button style={{marginTop: 5}} bsSize="small" onClick={this.clearAll}>Clear All</Button>
      </ButtonToolbar>
            );
    },
    renderCheckboxPanel() {
        return (
                <div>
                    {this.renderCheckboxElements()}
                    {(this.props.toolbar) ? this.renderToolbar() : null}
                </div>
            );
    },
    renderCombo() {
        let optionsValues = this.getOptionsValue();
        let options = optionsValues.map((o) => {
            return {val: o, text: this.props.valueFormatter(o, this.props.optionsLabels)};
        }, this);
        let val = (this.props.values && this.props.values.length > 0) ? {fieldValue: (this.props.multivalue) ? this.props.values : this.props.values[0] } : {};
        return (
            <div>
                    <ComboField
                    valueField="val"
                    textField="text"
                    style={this.props.comboStyle}
                    fieldOptions={options}
                    fieldName={this.props.attribute}
                    fieldRowId={this.props.fieldId}
                    attType={this.props.type}
                    multivalue={this.props.multivalue}
                    onUpdateField={this.onComboChange}
                    {...val}
                    />
                 {(this.props.toolbar && this.props.multivalue) ? this.renderToolbar() : null}
            </div>
            );
    },
    renderCheckOrRadio() {
        return (this.props.multivalue) ? this.renderCheckboxPanel() : this.renderRadioPanel();
    },
    renderText() {
        return (
                <TextField
                    operator={this.props.operator}
                    fieldName={this.props.attribute}
                    fieldRowId={this.props.fieldId}
                    fieldValue={this.props.values}
                    attType={this.props.type}
                    onUpdateField={this.onTextChange}
                    />
            );

    },
    renderNumber() {
        return (
                <NumberField
                    operator={"><"}
                    lowLabel={this.props.optionsLabels.lowLabel}
                    upLabel={this.props.optionsLabels.upLabel}
                    fieldName={this.props.attribute}
                    fieldRowId={this.props.fieldId}
                    fieldValue={this.props.values}
                    attType={this.props.type}
                    onUpdateField={this.onNumberChange}
                    onUpdateExceptionField={this.onNumberException}
                    fieldException={this.props.exception}
                    options={this.props.options}

                />);
    },
    renderList() {
        return (this.props.combo) ? this.renderCombo() : this.renderCheckOrRadio();
    },
    render() {
        let comp;
        switch (this.props.type) {
            case "list": {
                comp = this.renderList();
                break;
            }
            case "number": {
                comp = this.renderNumber();
                break;
            }
            case "string": {
                comp = this.renderText();
                break;
            }
            default: {
                comp = this.renderList();
            }
        }
        return (
            <Panel
                eventKey={this.props.eventKey || this.props.attribute}
                header={this.props.label || this.props.attribute}
                collapsible={this.props.collapsible}
                defaultExpanded={this.props.defaultExpanded}
                bsStyle={this.props.exception ? "danger" : "default"}>
                    {comp}
            </Panel>
            );
    },
    selectAll() {
        let values = this.getOptionsValue();
        this.props.updateFilter(this.props.fieldId, {values: values, exception: false});
    },
    clearAll() {
        this.props.updateFilter(this.props.fieldId, {values: [], exception: this.props.required});
    }

});

module.exports = SimpleFilterField;
