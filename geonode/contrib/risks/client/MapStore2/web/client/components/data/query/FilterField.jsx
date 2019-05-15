/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {Row, Col} = require('react-bootstrap');

const ComboField = require('./ComboField');
const assign = require('object-assign');

const FilterField = React.createClass({
    propTypes: {
        attributes: React.PropTypes.array,
        filterField: React.PropTypes.object,
        operatorOptions: React.PropTypes.array,
        onUpdateField: React.PropTypes.func,
        onUpdateExceptionField: React.PropTypes.func,
        onChangeCascadingValue: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            attributes: [],
            filterField: null,
            operatorOptions: ["=", ">", "<", ">=", "<=", "<>", "><"],
            onUpdateField: () => {},
            onUpdateExceptionField: () => {},
            onChangeCascadingValue: () => {}
        };
    },
    renderOperatorField() {
        return (
            <ComboField
                fieldOptions= {this.props.operatorOptions}
                fieldName="operator"
                fieldRowId={this.props.filterField.rowId}
                fieldValue={this.props.filterField.operator}
                onUpdateField={this.updateFieldElement}/>
        );
    },
    renderValueField(selectedAttribute) {
        const valueElement = React.cloneElement(
            React.Children.toArray(this.props.children).filter((node) => node.props.attType === selectedAttribute.type)[0],
            assign({
                fieldName: "value",
                fieldRowId: this.props.filterField.rowId,
                fieldValue: this.props.filterField.value,
                fieldException: this.props.filterField.exception,
                onUpdateField: this.updateFieldElement,
                onUpdateExceptionField: this.updateExceptionFieldElement
            }, selectedAttribute.fieldOptions || {})
        );

        return (
            valueElement
        );
    },
    render() {
        let selectedAttribute = this.props.attributes.filter((attribute) => attribute.attribute === this.props.filterField.attribute)[0];

        return (
            <div className="container-fluid">
                <Row className="filter-field-row">
                    <Col xs={4}>
                        <ComboField
                            valueField={'id'}
                            textField={'name'}
                            fieldOptions={this.props.attributes.map((attribute) => { return {id: attribute.attribute, name: attribute.label}; })}
                            fieldValue={this.props.filterField.attribute}
                            fieldName="attribute"
                            fieldRowId={this.props.filterField.rowId}
                            onUpdateField={this.updateFieldElement}
                            comboFilter={"contains"}/>
                    </Col>
                    <Col xs={3}>{selectedAttribute ? this.renderOperatorField() : null}</Col>
                    <Col xs={5}>{selectedAttribute && this.props.filterField.operator ? this.renderValueField(selectedAttribute) : null}</Col>
                </Row>
            </div>
        );
    },
    updateExceptionFieldElement(rowId, message) {
        this.props.onUpdateExceptionField(rowId, message);
    },
    updateFieldElement(rowId, name, value, type) {
        this.props.onUpdateField(rowId, name, value, type);

        if (name === "value") {
            // For cascading: filter the attributes that depends on
            let dependsOnAttributes = this.props.attributes.filter((attribute) => attribute.dependson && attribute.dependson.field === this.props.filterField.attribute);
            if (dependsOnAttributes.length > 0) {
                // Perhaps There is some filterFields that need to reset their value
                this.props.onChangeCascadingValue(dependsOnAttributes);
            }
        }
    }
});

module.exports = FilterField;
