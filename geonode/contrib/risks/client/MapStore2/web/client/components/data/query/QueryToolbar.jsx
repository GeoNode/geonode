/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {Button, Glyphicon, ButtonToolbar, Modal} = require('react-bootstrap');

const I18N = require('../../I18N/I18N');

const QueryToolbar = React.createClass({
    propTypes: {
        filterType: React.PropTypes.string,
        params: React.PropTypes.object,
        filterFields: React.PropTypes.array,
        groupFields: React.PropTypes.array,
        spatialField: React.PropTypes.object,
        toolbarEnabled: React.PropTypes.bool,
        searchUrl: React.PropTypes.string,
        showGeneratedFilter: React.PropTypes.oneOfType([
            React.PropTypes.bool,
            React.PropTypes.string
        ]),
        featureTypeName: React.PropTypes.string,
        actions: React.PropTypes.object,
        ogcVersion: React.PropTypes.string,
        resultTitle: React.PropTypes.string,
        pagination: React.PropTypes.object,
        sortOptions: React.PropTypes.object,
        hits: React.PropTypes.bool
    },
    getDefaultProps() {
        return {
            filterType: "OGC",
            params: {},
            groupFields: [],
            filterFields: [],
            spatialField: {},
            toolbarEnabled: true,
            searchUrl: null,
            showGeneratedFilter: false,
            featureTypeName: null,
            resultTitle: "Generated Filter",
            pagination: null,
            sortOptions: null,
            hits: false,
            actions: {
                onQuery: () => {},
                onReset: () => {},
                onChangeDrawingStatus: () => {}
            }
        };
    },
    render() {
        let fieldsExceptions = this.props.filterFields.filter((field) => field.exception).length > 0;
        // let fieldsWithoutValues = this.props.filterFields.filter((field) => !field.value).length > 0;
        let fieldsWithValues = this.props.filterFields.filter((field) => field.value).length > 0;

        let queryDisabled =
            // fieldsWithoutValues ||
            fieldsExceptions ||
            !this.props.toolbarEnabled ||
            (!fieldsWithValues && !this.props.spatialField.geometry);

        return (
            <div className="container-fluid query-toolbar">
                <div id="query-toolbar-title"><I18N.Message msgId={"queryform.title"}/></div>
                <ButtonToolbar className="queryFormToolbar row-fluid pull-right">
                    <Button disabled={!this.props.toolbarEnabled} bsSize="xs" id="reset" onClick={this.reset}>
                        <Glyphicon glyph="glyphicon glyphicon-refresh"/>
                        <span><strong><I18N.Message msgId={"queryform.reset"}/></strong></span>
                    </Button>
                    <Button disabled={queryDisabled} bsSize="xs" id="query" onClick={this.search}>
                        <Glyphicon glyph="glyphicon glyphicon-search"/>
                        <span><strong><I18N.Message msgId={"queryform.query"}/></strong></span>
                    </Button>
                </ButtonToolbar>
                <Modal show={this.props.showGeneratedFilter ? true : false} bsSize="large">
                    <Modal.Header>
                        <Modal.Title>{this.props.resultTitle}</Modal.Title>
                    </Modal.Header>
                    <Modal.Body>
                        <textarea style={{width: "862px", maxWidth: "862px", height: "236px", maxHeight: "236px"}}>{this.props.showGeneratedFilter}</textarea>
                    </Modal.Body>
                    <Modal.Footer>
                        <Button style={{"float": "right"}} onClick={() => this.props.actions.onQuery(null, null)}>Close</Button>
                    </Modal.Footer>
                </Modal>
            </div>
        );
    },
    search() {
        let filterObj = {
            featureTypeName: this.props.featureTypeName,
            groupFields: this.props.groupFields,
            filterFields: this.props.filterFields.filter((field) => field.value),
            spatialField: this.props.spatialField,
            pagination: this.props.pagination,
            filterType: this.props.filterType,
            ogcVersion: this.props.ogcVersion,
            sortOptions: this.props.sortOptions,
            hits: this.props.hits
        };
        this.props.actions.onQuery(this.props.searchUrl, filterObj, this.props.params);
    },
    reset() {
        this.props.actions.onChangeDrawingStatus('clean', null, "queryform", []);
        this.props.actions.onReset();
    }
});

module.exports = QueryToolbar;
