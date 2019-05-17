/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const Spinner = require('react-spinkit');
const Message = require('../../I18N/Message');
const ImporterUtils = require('../../../utils/ImporterUtils');
const {Table, Glyphicon, Button, Label, OverlayTrigger, Tooltip} = require('react-bootstrap');
const {findIndex} = require('lodash');

const ImportsGrid = React.createClass({
    propTypes: {
        loading: React.PropTypes.bool,
        timeout: React.PropTypes.number,
        loadImports: React.PropTypes.func,
        loadImport: React.PropTypes.func,
        deleteImport: React.PropTypes.func,
        imports: React.PropTypes.array,
        deleteAction: React.PropTypes.object,
        placement: React.PropTypes.string
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
             timeout: 5000,
            loadImports: () => {},
            placement: "bottom",
            deleteAction: <Message msgId="importer.import.deleteImport" />,
            loadImport: () => {},
            deleteImport: () => {},
            imports: []
        };
    },
    componentDidMount() {
        this.interval = setInterval(() => {this.update(); }, this.props.timeout);
    },
    componentWillUnmount() {
        clearInterval(this.interval);
    },
    getbsStyleForState(state) {
        return ImporterUtils.getbsStyleForState(state);
    },
    renderLoadingMessage(importObj) {
        switch (importObj.message) {
            case "deleting":
                return <Message msgId="importer.import.deleting" />;
            default:
                return null;
        }
    },
    renderLoadingImport(importObj) {
        if (importObj.loading) {
            return <div style={{"float": "right"}}>{this.renderLoadingMessage(importObj)}<Spinner noFadeIn overrideSpinnerClassName="spinner" spinnerName="circle"/></div>;
        }
        return null;
    },
    renderImportErrorMessage(imp) {
        if (imp && imp.error) {
            return <Label bsStyle="danger">{"Could not delete import, please try to delete all its content first"}</Label>;
        }
    },
    renderImport(importObj) {
        let tooltip = <Tooltip id="import-delete-action">{this.props.deleteAction}</Tooltip>;
        return (<tr key={importObj && importObj.id}>
                <td key="id"><a onClick={(e) => {e.preventDefault(); this.props.loadImport(importObj.id); }} >{importObj.id}</a></td>
                <td key="state"><Label bsStyle={this.getbsStyleForState(importObj.state)}>{importObj.state}</Label>
                {this.renderLoadingImport(importObj)}
                {this.renderImportErrorMessage(importObj)}
                </td>
                <td key="actions">
                    <OverlayTrigger overlay={tooltip} placement={this.props.placement}>
                        <Button bsSize="xsmall" onClick={(e) => {e.preventDefault(); this.props.deleteImport(importObj.id); }}><Glyphicon glyph="remove"/></Button>
                    </OverlayTrigger>
                </td>
            </tr>);
    },
    render() {
        if (this.props.loading && this.props.imports.length === 0) {
            return (<Spinner noFadeIn overrideSpinnerClassName="spinner" spinnerName="circle"/>);
        }
        return (
            <Table striped bordered condensed hover>
                <thead>
                    <tr>
                      <th><Message msgId="importer.number"/></th>
                      <th><Message msgId="importer.import.status" /></th>
                      <th><Message msgId="importer.import.actions" /></th>
                    </tr>
                </thead>
                <tbody>
                    {this.props.imports.map(this.renderImport)}
                </tbody>
            </Table>
        );
    },
    update() {
        if (this.props.imports) {
            let i = findIndex(this.props.imports, (importObj) => importObj.state === "RUNNING");
            if ( i >= 0 ) {
                this.props.loadImports();
            }
        }
    }
});
module.exports = ImportsGrid;
