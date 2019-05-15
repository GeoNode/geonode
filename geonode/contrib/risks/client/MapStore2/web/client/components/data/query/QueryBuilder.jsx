/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const GroupField = require('./GroupField');
const SpatialFilter = require('./SpatialFilter');
const QueryToolbar = require('./QueryToolbar');

const Spinner = require('react-spinkit');

require('./queryform.css');

const QueryBuilder = React.createClass({
    propTypes: {
        params: React.PropTypes.object,
        featureTypeConfigUrl: React.PropTypes.string,
        useMapProjection: React.PropTypes.bool,
        attributes: React.PropTypes.array,
        featureTypeError: React.PropTypes.string,
        featureTypeErrorText: React.PropTypes.node,
        groupLevels: React.PropTypes.number,
        filterFields: React.PropTypes.array,
        groupFields: React.PropTypes.array,
        spatialField: React.PropTypes.object,
        removeButtonIcon: React.PropTypes.string,
        addButtonIcon: React.PropTypes.string,
        attributePanelExpanded: React.PropTypes.bool,
        spatialPanelExpanded: React.PropTypes.bool,
        showDetailsPanel: React.PropTypes.bool,
        toolbarEnabled: React.PropTypes.bool,
        searchUrl: React.PropTypes.string,
        showGeneratedFilter: React.PropTypes.oneOfType([
            React.PropTypes.bool,
            React.PropTypes.string
        ]),
        filterType: React.PropTypes.string,
        featureTypeName: React.PropTypes.string,
        ogcVersion: React.PropTypes.string,
        attributeFilterActions: React.PropTypes.object,
        spatialFilterActions: React.PropTypes.object,
        queryToolbarActions: React.PropTypes.object,
        resultTitle: React.PropTypes.string,
        pagination: React.PropTypes.object,
        sortOptions: React.PropTypes.object,
        hits: React.PropTypes.bool,
        maxHeight: React.PropTypes.number
    },
    getDefaultProps() {
        return {
            params: {},
            featureTypeConfigUrl: null,
            useMapProjection: true,
            groupLevels: 1,
            groupFields: [],
            filterFields: [],
            attributes: [],
            featureTypeError: "",
            spatialField: {},
            removeButtonIcon: "glyphicon glyphicon-remove",
            addButtonIcon: "glyphicon glyphicon-plus",
            attributePanelExpanded: true,
            spatialPanelExpanded: true,
            showDetailsPanel: false,
            toolbarEnabled: true,
            searchUrl: "",
            showGeneratedFilter: false,
            featureTypeName: null,
            pagination: null,
            sortOptions: null,
            hits: false,
            maxHeight: 830,
            attributeFilterActions: {
                onAddGroupField: () => {},
                onAddFilterField: () => {},
                onRemoveFilterField: () => {},
                onUpdateFilterField: () => {},
                onUpdateExceptionField: () => {},
                onUpdateLogicCombo: () => {},
                onRemoveGroupField: () => {},
                onChangeCascadingValue: () => {},
                onExpandAttributeFilterPanel: () => {},
                onLoadFeatureTypeConfig: () => {}
            },
            spatialFilterActions: {
                onExpandSpatialFilterPanel: () => {},
                onSelectSpatialMethod: () => {},
                onSelectSpatialOperation: () => {},
                onChangeDrawingStatus: () => {},
                onRemoveSpatialSelection: () => {},
                onShowSpatialSelectionDetails: () => {},
                onEndDrawing: () => {},
                onChangeDwithinValue: () => {}
            },
            queryToolbarActions: {
                onQuery: () => {},
                onReset: () => {},
                onChangeDrawingStatus: () => {}
            }
        };
    },
    componentDidMount() {
        if (this.props.featureTypeConfigUrl && this.props.attributes.length < 1) {
            this.props.attributeFilterActions.onLoadFeatureTypeConfig(
                this.props.featureTypeConfigUrl, this.props.params);
        }
    },
    componentWillReceiveProps(props) {
        let url = props.featureTypeConfigUrl;
        let params = props.params !== this.props.params ? props.params : this.props.params;
        if (url !== this.props.featureTypeConfigUrl) {
            this.props.attributeFilterActions.onLoadFeatureTypeConfig(url, params);
        }
    },
    render() {
        if (this.props.featureTypeError !== "") {
            return (<div style={{margin: "0 auto", "text-align": "center"}}>{this.props.featureTypeErrorText}</div>);
        }
        return this.props.attributes.length > 0 ? (
            <div id="query-form-panel">
                <QueryToolbar
                    params={this.props.params}
                    filterFields={this.props.filterFields}
                    groupFields={this.props.groupFields}
                    spatialField={this.props.spatialField}
                    toolbarEnabled={this.props.toolbarEnabled}
                    searchUrl={this.props.searchUrl}
                    showGeneratedFilter={this.props.showGeneratedFilter}
                    featureTypeName={this.props.featureTypeName}
                    ogcVersion={this.props.ogcVersion}
                    filterType={this.props.filterType}
                    actions={this.props.queryToolbarActions}
                    resultTitle={this.props.resultTitle}
                    pagination={this.props.pagination}
                    sortOptions={this.props.sortOptions}
                    hits={this.props.hits}
                    />
                <div className="querypanel" style={{maxHeight: this.props.maxHeight - 170}}>
                    <GroupField
                        attributes={this.props.attributes}
                        groupLevels={this.props.groupLevels}
                        filterFields={this.props.filterFields}
                        groupFields={this.props.groupFields}
                        removeButtonIcon={this.props.removeButtonIcon}
                        addButtonIcon={this.props.addButtonIcon}
                        attributePanelExpanded={this.props.attributePanelExpanded}
                        actions={this.props.attributeFilterActions}/>
                    <SpatialFilter
                        useMapProjection={this.props.useMapProjection}
                        spatialField={this.props.spatialField}
                        spatialPanelExpanded={this.props.spatialPanelExpanded}
                        showDetailsPanel={this.props.showDetailsPanel}
                        actions={this.props.spatialFilterActions}/>
                </div>
            </div>
        ) : (<div style={{margin: "0 auto", width: "60px"}}><Spinner spinnerName="three-bounce" overrideSpinnerClassName="spinner"/></div>);
    }
});

module.exports = QueryBuilder;
