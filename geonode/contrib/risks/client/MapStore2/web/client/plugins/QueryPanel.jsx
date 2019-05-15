/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {connect} = require('react-redux');
const Sidebar = require('react-sidebar').default;
const {createSelector} = require('reselect');
const {changeLayerProperties, changeGroupProperties, toggleNode,
       sortNode, showSettings, hideSettings, updateSettings, updateNode, removeNode} = require('../actions/layers');

const {getLayerCapabilities} = require('../actions/layerCapabilities');

const {zoomToExtent} = require('../actions/map');
const {toggleControl} = require('../actions/controls');

const {groupsSelector} = require('../selectors/layers');

const LayersUtils = require('../utils/LayersUtils');

// include application component
const QueryBuilder = require('../components/data/query/QueryBuilder');

const {bindActionCreators} = require('redux');
const {
    // QueryBuilder action functions
    addGroupField,
    addFilterField,
    removeFilterField,
    updateFilterField,
    updateExceptionField,
    updateLogicCombo,
    removeGroupField,
    changeCascadingValue,
    expandAttributeFilterPanel,
    expandSpatialFilterPanel,
    selectSpatialMethod,
    selectSpatialOperation,
    removeSpatialSelection,
    showSpatialSelectionDetails,
    reset,
    changeDwithinValue,
    zoneGetValues,
    zoneSearch,
    zoneChange
} = require('../actions/queryform');

const {createQuery} = require('../actions/wfsquery');

const {
    changeDrawingStatus,
    endDrawing
} = require('../actions/draw');

// connecting a Dumb component to the store
// makes it a smart component
// we both connect state => props
// and actions to event handlers
const SmartQueryForm = connect((state) => {
    return {
        // QueryBuilder props
        useMapProjection: state.queryform.useMapProjection,
        groupLevels: state.queryform.groupLevels,
        groupFields: state.queryform.groupFields,
        filterFields: state.queryform.filterFields,
        spatialField: state.queryform.spatialField,
        showDetailsPanel: state.queryform.showDetailsPanel,
        toolbarEnabled: state.queryform.toolbarEnabled,
        attributePanelExpanded: state.queryform.attributePanelExpanded,
        spatialPanelExpanded: state.queryform.spatialPanelExpanded,
        searchUrl: "http://demo.geo-solutions.it/geoserver/ows?service=WFS",
        featureTypeName: "topp:states",
        ogcVersion: "1.1.0",
        resultTitle: "Query Result",
        showGeneratedFilter: false
    };
}, dispatch => {
    return {
        attributeFilterActions: bindActionCreators({
            onAddGroupField: addGroupField,
            onAddFilterField: addFilterField,
            onRemoveFilterField: removeFilterField,
            onUpdateFilterField: updateFilterField,
            onUpdateExceptionField: updateExceptionField,
            onUpdateLogicCombo: updateLogicCombo,
            onRemoveGroupField: removeGroupField,
            onChangeCascadingValue: changeCascadingValue,
            onExpandAttributeFilterPanel: expandAttributeFilterPanel
        }, dispatch),
        spatialFilterActions: bindActionCreators({
            onExpandSpatialFilterPanel: expandSpatialFilterPanel,
            onSelectSpatialMethod: selectSpatialMethod,
            onSelectSpatialOperation: selectSpatialOperation,
            onChangeDrawingStatus: changeDrawingStatus,
            onRemoveSpatialSelection: removeSpatialSelection,
            onShowSpatialSelectionDetails: showSpatialSelectionDetails,
            onEndDrawing: endDrawing,
            onChangeDwithinValue: changeDwithinValue,
            zoneFilter: zoneGetValues,
            zoneSearch,
            zoneChange
        }, dispatch),
        queryToolbarActions: bindActionCreators({
            onQuery: createQuery,
            onReset: reset,
            onChangeDrawingStatus: changeDrawingStatus
        }, dispatch)
    };
})(QueryBuilder);

const tocSelector = createSelector(
    [
        (state) => state.controls && state.controls.toolbar && state.controls.toolbar.active === 'toc',
        groupsSelector,
        (state) => state.layers && state.layers.settings || {expanded: false, options: {opacity: 1}},
        (state) => state.controls && state.controls.queryPanel && state.controls.queryPanel.enabled || false
    ], (enabled, groups, settings, querypanelEnabled) => ({
        enabled,
        groups,
        settings,
        querypanelEnabled
    })
);

const LayerTree = React.createClass({
    propTypes: {
        id: React.PropTypes.number,
        buttonContent: React.PropTypes.node,
        groups: React.PropTypes.array,
        settings: React.PropTypes.object,
        querypanelEnabled: React.PropTypes.bool,
        groupStyle: React.PropTypes.object,
        groupPropertiesChangeHandler: React.PropTypes.func,
        layerPropertiesChangeHandler: React.PropTypes.func,
        onToggleGroup: React.PropTypes.func,
        onToggleLayer: React.PropTypes.func,
        onToggleQuery: React.PropTypes.func,
        onZoomToExtent: React.PropTypes.func,
        retrieveLayerData: React.PropTypes.func,
        onSort: React.PropTypes.func,
        onSettings: React.PropTypes.func,
        hideSettings: React.PropTypes.func,
        updateSettings: React.PropTypes.func,
        updateNode: React.PropTypes.func,
        removeNode: React.PropTypes.func,
        activateRemoveLayer: React.PropTypes.bool,
        activateLegendTool: React.PropTypes.bool,
        activateZoomTool: React.PropTypes.bool,
        activateSettingsTool: React.PropTypes.bool,
        visibilityCheckType: React.PropTypes.string,
        settingsOptions: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            groupPropertiesChangeHandler: () => {},
            layerPropertiesChangeHandler: () => {},
            retrieveLayerData: () => {},
            onToggleGroup: () => {},
            onToggleLayer: () => {},
            onToggleQuery: () => {},
            onZoomToExtent: () => {},
            onSettings: () => {},
            updateNode: () => {},
            removeNode: () => {},
            activateLegendTool: true,
            activateZoomTool: true,
            activateSettingsTool: true,
            activateRemoveLayer: true,
            visibilityCheckType: "checkbox",
            settingsOptions: {},
            querypanelEnabled: false
        };
    },
    getNoBackgroundLayers(group) {
        return group.name !== 'background';
    },
    renderSidebar() {
        return (
            <Sidebar
                open={this.props.querypanelEnabled}
                sidebar={this.renderQueryPanel()}
                styles={{
                        sidebar: {
                            backgroundColor: 'white',
                            zIndex: 1024,
                            width: 600
                        },
                        overlay: {
                            zIndex: 1023,
                            width: 0
                        },
                         root: {
                             right: this.props.querypanelEnabled ? 0 : 'auto',
                             width: '0',
                             overflow: 'visible'
                         }
                    }}
                >
                <div/>
            </Sidebar>
        );
    },
    renderQueryPanel() {
        return (<div>
            <SmartQueryForm/>
        </div>);
    },
    render() {
        return this.renderSidebar();
    }
});

const QueryPanelPlugin = connect(tocSelector, {
    groupPropertiesChangeHandler: changeGroupProperties,
    layerPropertiesChangeHandler: changeLayerProperties,
    retrieveLayerData: getLayerCapabilities,
    onToggleGroup: LayersUtils.toggleByType('groups', toggleNode),
    onToggleLayer: LayersUtils.toggleByType('layers', toggleNode),
    onToggleQuery: toggleControl.bind(null, 'queryPanel', null),
    onSort: LayersUtils.sortUsing(LayersUtils.sortLayers, sortNode),
    onSettings: showSettings,
    onZoomToExtent: zoomToExtent,
    hideSettings,
    updateSettings,
    updateNode,
    removeNode
})(LayerTree);

module.exports = {
    QueryPanelPlugin,
    reducers: {
        queryform: require('../reducers/queryform'),
        query: require('../reducers/query')
    }
};
