/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {Row, Col, Panel, Button, Glyphicon, FormControl} = require('react-bootstrap');
const ComboField = require('./ComboField');
const GeometryDetails = require('./GeometryDetails');

const ZoneField = require('./ZoneField');

const LocaleUtils = require('../../../utils/LocaleUtils');
const I18N = require('../../I18N/I18N');

const SpatialFilter = React.createClass({
    propTypes: {
        useMapProjection: React.PropTypes.bool,
        spatialField: React.PropTypes.object,
        spatialOperations: React.PropTypes.array,
        spatialMethodOptions: React.PropTypes.array,
        spatialPanelExpanded: React.PropTypes.bool,
        showDetailsPanel: React.PropTypes.bool,
        withContainer: React.PropTypes.bool,
        actions: React.PropTypes.object
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            useMapProjection: true,
            spatialField: {},
            spatialPanelExpanded: true,
            showDetailsPanel: false,
            withContainer: true,
            spatialMethodOptions: [
                {id: "BBOX", name: "queryform.spatialfilter.methods.box"},
                {id: "Circle", name: "queryform.spatialfilter.methods.circle"},
                {id: "Polygon", name: "queryform.spatialfilter.methods.poly"}
            ],
            spatialOperations: [
                {id: "INTERSECTS", name: "queryform.spatialfilter.operations.intersects"},
                {id: "BBOX", name: "queryform.spatialfilter.operations.bbox"},
                {id: "CONTAINS", name: "queryform.spatialfilter.operations.contains"},
                {id: "DWITHIN", name: "queryform.spatialfilter.operations.dwithin"},
                {id: "WITHIN", name: "queryform.spatialfilter.operations.within"}
            ],
            actions: {
                onExpandSpatialFilterPanel: () => {},
                onSelectSpatialMethod: () => {},
                onSelectSpatialOperation: () => {},
                onChangeDrawingStatus: () => {},
                onRemoveSpatialSelection: () => {},
                onShowSpatialSelectionDetails: () => {},
                onEndDrawing: () => {},
                onChangeDwithinValue: () => {},
                zoneFilter: () => {},
                zoneSearch: () => {},
                // openMenu: () => {},
                zoneChange: () => {}
                // zoneSelect: () => {}
            }
        };
    },
    renderHeader() {
        const spatialFilterHeader = LocaleUtils.getMessageById(this.context.messages, "queryform.spatialfilter.spatial_filter_header");

        return (
            <span>
                <span
                    style={{cursor: "pointer"}}
                    onClick={this.props.actions.onExpandSpatialFilterPanel.bind(null, !this.props.spatialPanelExpanded)}>{spatialFilterHeader}</span>
                <button onClick={this.props.actions.onExpandSpatialFilterPanel.bind(null, !this.props.spatialPanelExpanded)} className="close">
                    {this.props.spatialPanelExpanded ? <Glyphicon glyph="glyphicon glyphicon-collapse-down"/> : <Glyphicon glyph="glyphicon glyphicon-expand"/>}
                </button>
            </span>
        );
    },
    renderSpatialHeader() {
        const selectedMethod = this.props.spatialMethodOptions.filter((opt) => this.props.spatialField.method === opt.id)[0];

        const methodCombo = (
            <ComboField
                fieldOptions={
                    this.props.spatialMethodOptions.map((opt) => {
                        return LocaleUtils.getMessageById(this.context.messages, opt.name);
                    })
                }
                fieldName="method"
                style={{width: "140px"}}
                fieldRowId={new Date().getUTCMilliseconds()}
                fieldValue={
                    LocaleUtils.getMessageById(this.context.messages, selectedMethod ? selectedMethod.name : "")
                }
                onUpdateField={this.updateSpatialMethod}/>
        );

        const detailsButton = this.props.spatialField.geometry && (this.props.spatialField.method === "BBOX" || this.props.spatialField.method === "Circle") ? (
            <Button id="remove-filter-field" className="filter-buttons" bsSize="xs" style={{border: 'none'}} onClick={() => this.props.actions.onShowSpatialSelectionDetails(true)}>
                <Glyphicon glyph={'glyphicon glyphicon-plus'}/><I18N.Message msgId={"queryform.spatialfilter.details.detail_button_label"}/>
            </Button>
        ) : (
            <span/>
        );

        const resetButton = this.props.spatialField.geometry && this.props.spatialField.geometry.coordinates ? (
            <Button className="remove-filter-button" onClick={() => this.resetSpatialFilter()}>
                <Glyphicon glyph="glyphicon glyphicon-remove"/>
            </Button>
        ) : (
            <span/>
        );

        const methodSelector = this.props.spatialField.geometry ? (
            <Row className="logicHeader filter-field-row">
                <Col xs={5}>
                    <div><I18N.Message msgId={"queryform.spatialfilter.selection_method"}/></div>
                </Col>
                <Col xs={3}>
                    {methodCombo}
                </Col>
                <Col xs={2} className="detail_geom_button filter-text-desc">
                    {detailsButton}
                </Col>
                <Col xs={2} className="detail_geom_button">
                    {resetButton}
                </Col>
            </Row>
        ) : (
            <Row className="logicHeader filter-field-row">
                <Col xs={5}>
                    <div><I18N.Message msgId={"queryform.spatialfilter.selection_method"}/></div>
                </Col>
                <Col xs={7}>
                    {methodCombo}
                </Col>
            </Row>
        );

        return (
            <div className="container-fluid">
                {methodSelector}
            </div>
        );
    },
    renderZoneFields() {
        return this.props.spatialField.method &&
            this.props.spatialField.method === "ZONE" &&
            this.props.spatialField.zoneFields &&
            this.props.spatialField.zoneFields.length > 0 ?
                this.props.spatialField.zoneFields.map((zone) => {
                    return (
                        <ZoneField
                            key={zone.id}
                            open={zone.open}
                            zoneId={zone.id}
                            url={zone.url}
                            typeName={zone.typeName}
                            wfs={zone.wfs}
                            busy={zone.busy}
                            label={zone.label}
                            values={zone.values}
                            value={zone.value}
                            valueField={zone.valueField}
                            textField={zone.textField}
                            searchText={zone.searchText}
                            searchMethod={zone.searchMethod}
                            searchAttribute={zone.searchAttribute}
                            sort={zone.sort}
                            error={zone.error}
                            disabled={zone.disabled}
                            dependsOn={zone.dependson}
                            groupBy={zone.groupBy}
                            multivalue={zone.multivalue}
                            onSearch={this.props.actions.zoneSearch}
                            onFilter={this.props.actions.zoneFilter}
                            // onOpenMenu={this.props.actions.openMenu}
                            // onSelect={this.props.actions.zoneSelect}
                            onChange={this.props.actions.zoneChange}/>
                    );
                }) : (<span/>);
    },
    renderSpatialPanel(operationRow, drawLabel) {
        return (
            <Panel>
                {this.props.spatialMethodOptions.length > 1 ? this.renderSpatialHeader() : <span/>}
                {this.renderZoneFields()}
                {this.props.spatialOperations.length > 1 ? (
                    <Panel>
                        <div className="container-fluid">
                            {operationRow}
                        </div>
                        <Row>
                            <Col xs={12}>
                                {drawLabel}
                            </Col>
                        </Row>
                    </Panel>
                ) : (
                    <span/>
                )}
            </Panel>
        );
    },
    render() {
        const selectedOperation = this.props.spatialOperations.filter((opt) => this.props.spatialField.operation === opt.id)[0];

        let drawLabel = (<span/>);
        if (this.props.spatialField.method && this.props.spatialField.method !== "ZONE") {
            drawLabel = !this.props.spatialField.geometry ? (
                <span>
                    <hr width="100%"/>
                    <div><h5><I18N.Message msgId={"queryform.spatialfilter.draw_start_label"}/></h5></div>
                </span>
            ) : (
                <span/>
            );
        }

        const detailsPanel = this.props.showDetailsPanel ? (
            <GeometryDetails
                useMapProjection={this.props.useMapProjection}
                geometry={this.props.spatialField.geometry}
                type={this.props.spatialField.method}
                onShowPanel={this.props.actions.onShowSpatialSelectionDetails}
                onChangeDrawingStatus={this.changeDrawingStatus}
                onEndDrawing={this.props.actions.onEndDrawing}/>
        ) : (
            <span/>
        );

        const operationRow = selectedOperation && selectedOperation.id === "DWITHIN" ? (
            <Row className="filter-field-row">
                <Col xs={5}>
                    <I18N.Message msgId={"queryform.spatialfilter.geometric_operation"}/>
                </Col>
                <Col xs={3}>
                    <ComboField
                        fieldOptions={
                            this.props.spatialOperations.map((opt) => {
                                return LocaleUtils.getMessageById(this.context.messages, opt.name);
                            })
                        }
                        fieldName="operation"
                        style={{width: "140px"}}
                        fieldRowId={new Date().getUTCMilliseconds()}
                        fieldValue={
                            LocaleUtils.getMessageById(this.context.messages, selectedOperation ? selectedOperation.name : "")
                        }
                        onUpdateField={this.updateSpatialOperation}/>
                </Col>
                <Col xs={2} className="filter-text-desc">
                    <I18N.Message msgId={"queryform.spatialfilter.dwithin_label"}/>{':'}
                </Col>
                <Col xs={2}>
                        <FormControl
                            type="number"
                            min="0"
                            defaultValue="0"
                            disabled={!this.props.spatialField.geometry}
                            id={"queryform_dwithin_field"}
                            onChange={(evt) => this.props.actions.onChangeDwithinValue(evt.target.value, name)}/>
                </Col>
            </Row>
        ) : (
            <Row className="filter-field-row">
                <Col xs={5}>
                    <I18N.Message msgId={"queryform.spatialfilter.geometric_operation"}/>
                </Col>
                <Col xs={7}>
                    <ComboField
                        fieldOptions={
                            this.props.spatialOperations.map((opt) => {
                                return LocaleUtils.getMessageById(this.context.messages, opt.name);
                            })
                        }
                        fieldName="operation"
                        style={{width: "140px"}}
                        fieldRowId={new Date().getUTCMilliseconds()}
                        fieldValue={
                            LocaleUtils.getMessageById(this.context.messages, selectedOperation ? selectedOperation.name : "")
                        }
                        onUpdateField={this.updateSpatialOperation}/>
                </Col>
            </Row>
        );

        return (
            <div className="query-filter-container">
                {
                    this.props.withContainer ? (
                        <Panel id="spatialFilterPanel" collapsible expanded={this.props.spatialPanelExpanded} header={this.renderHeader()}>
                            {this.renderSpatialPanel(operationRow, drawLabel)}
                        </Panel>
                    ) : this.renderSpatialPanel(operationRow, drawLabel)
                }
                {detailsPanel}
            </div>
        );
    },
    updateSpatialMethod(id, name, value) {
        this.props.actions.onShowSpatialSelectionDetails(false);

        const method = this.props.spatialMethodOptions.filter((opt) => {
            if (value === LocaleUtils.getMessageById(this.context.messages, opt.name)) {
                return opt;
            }
        })[0].id;

        this.props.actions.onSelectSpatialMethod(method, name);

        if (method !== "ZONE") {
            this.changeDrawingStatus('start', method, "queryform", []);
        } else {
            this.changeDrawingStatus('clean', null, "queryform", []);
        }
    },
    updateSpatialOperation(id, name, value) {
        const opeartion = this.props.spatialOperations.filter((opt) => {
            if (value === LocaleUtils.getMessageById(this.context.messages, opt.name)) {
                return opt;
            }
        })[0].id;

        this.props.actions.onSelectSpatialOperation(opeartion, name);
    },
    resetSpatialFilter() {
        this.changeDrawingStatus('clean', null, "queryform", []);
        this.props.actions.onRemoveSpatialSelection();
        this.props.actions.onShowSpatialSelectionDetails(false);
    },
    changeDrawingStatus(status, method, owner, features) {
        this.props.actions.onChangeDrawingStatus(
            status,
            method !== undefined ? method : this.props.spatialField.method,
            owner,
            features);
    }
});

module.exports = SpatialFilter;
