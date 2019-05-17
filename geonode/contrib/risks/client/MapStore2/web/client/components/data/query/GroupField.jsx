/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {Row, Col, Button, Glyphicon, Panel, OverlayTrigger, Tooltip} = require('react-bootstrap');

const FilterField = require('./FilterField');
const ComboField = require('./ComboField');
const DateField = require('./DateField');
const NumberField = require('./NumberField');
const TextField = require('./TextField');

const LocaleUtils = require('../../../utils/LocaleUtils');
const I18N = require('../../I18N/I18N');

const GroupField = React.createClass({
    propTypes: {
        groupLevels: React.PropTypes.number,
        groupFields: React.PropTypes.array,
        filterFields: React.PropTypes.array,
        attributes: React.PropTypes.array,
        fieldWidth: React.PropTypes.string,
        removeButtonIcon: React.PropTypes.string,
        addButtonIcon: React.PropTypes.string,
        logicComboOptions: React.PropTypes.array,
        attributePanelExpanded: React.PropTypes.bool,
        actions: React.PropTypes.object
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            groupLevels: 1,
            groupFields: [],
            filterFields: [],
            attributes: [],
            removeButtonIcon: "glyphicon glyphicon-minus",
            addButtonIcon: "glyphicon glyphicon-plus",
            attributePanelExpanded: true,
            logicComboOptions: [
                {logic: "OR", name: "queryform.attributefilter.groupField.any"},
                {logic: "AND", name: "queryform.attributefilter.groupField.all"},
                {logic: "AND NOT", name: "queryform.attributefilter.groupField.none"}
            ],
            actions: {
                onAddGroupField: () => {},
                onAddFilterField: () => {},
                onRemoveFilterField: () => {},
                onUpdateFilterField: () => {},
                onUpdateExceptionField: () => {},
                onUpdateLogicCombo: () => {},
                onRemoveGroupField: () => {},
                onChangeCascadingValue: () => {},
                onExpandAttributeFilterPanel: () => {}
            }
        };
    },
    getComboValues(selected, attributes) {
        if (selected && selected.dependson) {
            // ///////////////////////////////////////////////////////////////////////////
            // Retrieving the filterField which depends the selected one (the main field)
            // ///////////////////////////////////////////////////////////////////////////
            let filterField = this.props.filterFields.filter((field) => field.attribute === selected.dependson.field)[0];
            if (filterField && filterField.value) {
                // The complete attribute config object
                let attribute = attributes.filter((attr) => attr.attribute === filterField.attribute)[0];
                // The reference ID of the related attribute field value
                let attributeRefId = attribute.values.filter((value) => value[attribute.valueId] === filterField.value)[0][selected.dependson.from];
                // The filtered values that match the attribute refId
                let values = selected.values.filter((value) => value[selected.dependson.to] === attributeRefId);

                return (selected && selected.type === "list" ? values.map((value) => {
                    return {id: (selected.fidPrefix ? selected.fidPrefix + "." + value[selected.valueId] : value[selected.valueId]), name: value[selected.valueLabel]};
                }) : null);
            }
        }

        return (selected && selected.type === "list" ? selected.values.map((value) => {
            return {id: (selected.fidPrefix ? selected.fidPrefix + "." + value[selected.valueId] : value[selected.valueId]), name: value[selected.valueLabel]};
        }) : null);
    },
    getOperator(selectedAttribute) {
        let type = (selectedAttribute && selectedAttribute.type) ? selectedAttribute.type : "";
        switch (type) {
            case "list": {
                return ["="];
            }
            case "string": {
                return ["=", "like", "ilike", "isNull"];
            }
            default:
                return ["=", ">", "<", ">=", "<=", "<>", "><"];
        }
    },
    renderFilterField(filterField) {
        let selectedAttribute = this.props.attributes.filter((attribute) => attribute.attribute === filterField.attribute)[0];
        let comboValues = this.getComboValues(selectedAttribute, this.props.attributes);

        return (
            <div className="container-fluid" key={filterField.rowId}>
                <Row className="filter-field-row">
                    <Col xs={10}>
                        <FilterField
                            attributes={this.props.attributes}
                            filterField={filterField}
                            operatorOptions={this.getOperator(selectedAttribute)}
                            onUpdateField={this.props.actions.onUpdateFilterField}
                            onUpdateExceptionField={this.props.actions.onUpdateExceptionField}
                            onChangeCascadingValue={this.props.actions.onChangeCascadingValue}>
                            <ComboField
                                attType="list"
                                valueField={'id'}
                                textField={'name'}
                                fieldOptions={comboValues ? comboValues : []}
                                comboFilter={"contains"}/>
                            <DateField
                                attType="date"
                                operator={filterField.operator}/>
                            <NumberField
                                operator={filterField.operator}
                                attType="number"/>
                            <TextField
                                operator={filterField.operator}
                                attType="string"/>
                        </FilterField>
                    </Col>
                    <Col xs={2}>
                        {
                            filterField.exception ? (
                                <OverlayTrigger placement="bottom" overlay={(<Tooltip id={filterField.rowId + "tooltip"}><strong><I18N.Message msgId={filterField.exception || ""}/></strong></Tooltip>)}>
                                    <Button id="remove-filter-field" className="remove-filter-button" style={{backgroundColor: "red"}} onClick={() => this.props.actions.onRemoveFilterField(filterField.rowId)}>
                                        <Glyphicon style={{color: "white"}} glyph="glyphicon glyphicon-warning-sign"/>
                                    </Button>
                                </OverlayTrigger>
                            ) : (
                                <Button id="remove-filter-field" className="remove-filter-button" onClick={() => this.props.actions.onRemoveFilterField(filterField.rowId)}>
                                    <Glyphicon glyph={this.props.removeButtonIcon}/>
                                </Button>
                            )
                        }
                    </Col>
                </Row>
            </div>
        );
    },
    renderGroupHeader(groupField) {
        const removeButton = groupField.groupId ?
            (
                    <Button bsSize="xs" className="remove-filter-button" onClick={() => this.props.actions.onRemoveGroupField(groupField.id)}>
                        <Glyphicon glyph={this.props.removeButtonIcon}/>
                    </Button>
            ) : (
                <Col xs={0} lgHidden={true}>
                    <span/>
                </Col>
            );

        return (
            <div className="container-fluid">
                <Row className="logicHeader filter-field-row">
                    <Col xs={10}>
                        <div className="container-fluid">
                            <Row className="filter-field-row">
                                <div className="filter-logig-header-text">
                                    <span className="group_label_a"><I18N.Message msgId={"queryform.attributefilter.group_label_a"}/></span>
                                </div>
                                <div className="filter-logig-header-text">
                                    <ComboField
                                        fieldOptions={
                                            this.props.logicComboOptions.map((opt) => {
                                                return LocaleUtils.getMessageById(this.context.messages, opt.name);
                                            })
                                        }
                                        fieldName="logic"
                                        style={{minWidth: "80px"}}
                                        fieldRowId={groupField.id}
                                        fieldValue={
                                            LocaleUtils.getMessageById(this.context.messages,
                                                this.props.logicComboOptions.filter((opt) => groupField.logic === opt.logic)[0].name)
                                        }
                                        onUpdateField={this.updateLogicCombo}/>
                                </div>
                                <div className="filter-logig-header-text">
                                    <span className="group_label_b"><I18N.Message msgId={"queryform.attributefilter.group_label_b"}/></span>
                                </div>
                            </Row>
                        </div>
                    </Col>
                    <Col xs={2}>
                        <div className="query-remove">
                            {removeButton}
                        </div>
                    </Col>
                </Row>
            </div>
        );
    },
    renderGroupField(groupField) {
        const filterFields = this.props.filterFields.filter((filterField) => filterField.groupId === groupField.id);
        const groupFields = this.props.groupFields.filter((group) => group.groupId === groupField.id);

        const fields = [...filterFields, ...groupFields];

        const container = fields.map((field) => {
            let element;
            if (field.rowId !== undefined) {
                element = this.renderFilterField(field);
            } else {
                element = this.renderGroupField(field);
            }

            return element;
        });

        const addButton = groupField.index <= this.props.groupLevels ?
            (
                <Button id="add-condition-group" className="filter-buttons" bsSize="xs" onClick={() => this.props.actions.onAddGroupField(groupField.id, groupField.index)}>
                    <Glyphicon glyph={this.props.addButtonIcon}/><I18N.Message msgId={"queryform.attributefilter.add_group"}/></Button>
            ) : (
                <span/>
            );

        return (
            <Panel className="filter-group-panel" key={groupField.id}>
                {this.renderGroupHeader(groupField)}
                <div className="query-content">{container}</div>
                <div className="query-buttons">
                {addButton}
                <Button id="add-filter-field" className="filter-buttons" bsSize="xs" onClick={() => this.props.actions.onAddFilterField(groupField.id)}>
                    <Glyphicon glyph={this.props.addButtonIcon}/>
                    <I18N.Message msgId={"queryform.attributefilter.add_condition"}/>
                </Button>
                </div>
            </Panel>
        );
    },
    renderHeader() {
        const attributeFilterHeader = LocaleUtils.getMessageById(this.context.messages, "queryform.attributefilter.attribute_filter_header");

        return (
            <span>
                <span
                    style={{cursor: "pointer"}}
                    onClick={this.props.actions.onExpandAttributeFilterPanel.bind(null, !this.props.attributePanelExpanded)}>{attributeFilterHeader}</span>
                <button onClick={this.props.actions.onExpandAttributeFilterPanel.bind(null, !this.props.attributePanelExpanded)} className="close">
                    {this.props.attributePanelExpanded ? <Glyphicon glyph="glyphicon glyphicon-collapse-down"/> : <Glyphicon glyph="glyphicon glyphicon-expand"/>}
                </button>
            </span>
        );
    },
    render() {
        return (
            <Panel id="attributeFilterPanel" className="query-filter-container" collapsible
                expanded={this.props.attributePanelExpanded}
                header={this.renderHeader()}>
                {this.props.groupFields.filter(g => !g.groupId).map(this.renderGroupField)}
            </Panel>
        );
    },
    updateLogicCombo(groupId, name, value) {
        const logic = this.props.logicComboOptions.filter((opt) => {
            if (value === LocaleUtils.getMessageById(this.context.messages, opt.name)) {
                return opt;
            }
        })[0].logic;
        this.props.actions.onUpdateLogicCombo(groupId, logic);
    }
});

module.exports = GroupField;
