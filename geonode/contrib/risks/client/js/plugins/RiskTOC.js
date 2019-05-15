/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {connect} = require('react-redux');
const {createSelector} = require('reselect');

const {changeLayerProperties, changeGroupProperties, toggleNode,
       sortNode, showSettings, hideSettings, updateSettings, updateNode, removeNode} = require('../../MapStore2/web/client/actions/layers');
const {getLayerCapabilities} = require('../../MapStore2/web/client/actions/layerCapabilities');
const {zoomToExtent} = require('../../MapStore2/web/client/actions/map');
const {groupsSelector} = require('../../MapStore2/web/client/selectors/layers');

const LayersUtils = require('../../MapStore2/web/client/utils/LayersUtils');

const Message = require('../../MapStore2/web/client/plugins/locale/Message');

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

const TOC = require('../../MapStore2/web/client/components/TOC/TOC');
const DefaultGroup = require('../../MapStore2/web/client/components/TOC/DefaultGroup');
const DefaultLayer = require('../../MapStore2/web/client/components/TOC/DefaultLayer');
const DefaultLayerOrGroup = require('../../MapStore2/web/client/components/TOC/DefaultLayerOrGroup');

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
        activateQueryTool: React.PropTypes.bool,
        activateSettingsTool: React.PropTypes.bool,
        visibilityCheckType: React.PropTypes.string,
        settingsOptions: React.PropTypes.object,
        enabled: React.PropTypes.bool
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
            activateLegendTool: false,
            activateZoomTool: false,
            activateSettingsTool: false,
            activateRemoveLayer: false,
            activateQueryTool: false,
            visibilityCheckType: "glyph",
            settingsOptions: {
                includeCloseButton: false,
                closeGlyph: "1-close",
                asModal: false,
                buttonSize: "small"
            },
            querypanelEnabled: false
        };
    },
    getNoBackgroundLayers(group) {
        return group.name !== 'background';
    },
    renderTOC() {
        const Group = (<DefaultGroup onSort={this.props.onSort}
                                  propertiesChangeHandler={this.props.groupPropertiesChangeHandler}
                                  onToggle={this.props.onToggleGroup}
                                  style={this.props.groupStyle}
                                  groupVisibilityCheckbox={true}
                                  visibilityCheckType={this.props.visibilityCheckType}
                                  />);
        const Layer = (<DefaultLayer
                            settingsOptions={this.props.settingsOptions}
                            onToggle={this.props.onToggleLayer}
                            onToggleQuerypanel={this.props.onToggleQuery }
                            onZoom={this.props.onZoomToExtent}
                            onSettings={this.props.onSettings}
                            propertiesChangeHandler={this.props.layerPropertiesChangeHandler}
                            hideSettings={this.props.hideSettings}
                            settings={this.props.settings}
                            updateSettings={this.props.updateSettings}
                            updateNode={this.props.updateNode}
                            removeNode={this.props.removeNode}
                            visibilityCheckType={this.props.visibilityCheckType}
                            activateRemoveLayer={this.props.activateRemoveLayer}
                            activateLegendTool={this.props.activateLegendTool}
                            activateZoomTool={this.props.activateZoomTool}
                            activateQueryTool={this.props.activateQueryTool}
                            activateSettingsTool={this.props.activateSettingsTool}
                            retrieveLayerData={this.props.retrieveLayerData}
                            settingsText={<Message msgId="layerProperties.windowTitle"/>}
                            opacityText={<Message msgId="opacity"/>}
                            saveText={<Message msgId="save"/>}
                            closeText={<Message msgId="close"/>}
                            groups={this.props.groups}/>);
        return (
            <div className="risk-toc-container">
                <TOC onSort={this.props.onSort} filter={this.getNoBackgroundLayers}
                    nodes={this.props.groups}>
                    <DefaultLayerOrGroup groupElement={Group} layerElement={Layer}/>
                </TOC>
            </div>
        );
    },
    render() {
        if (!this.props.groups || !this.props.enabled) {
            return null;
        }
        return this.renderTOC();
    }
});

const TOCPlugin = connect(tocSelector, {
    groupPropertiesChangeHandler: changeGroupProperties,
    layerPropertiesChangeHandler: changeLayerProperties,
    retrieveLayerData: getLayerCapabilities,
    onToggleGroup: LayersUtils.toggleByType('groups', toggleNode),
    onToggleLayer: LayersUtils.toggleByType('layers', toggleNode),
    onSort: LayersUtils.sortUsing(LayersUtils.sortLayers, sortNode),
    onSettings: showSettings,
    onZoomToExtent: zoomToExtent,
    hideSettings,
    updateSettings,
    updateNode,
    removeNode
})(LayerTree);

module.exports = {
    TOCPlugin
};
