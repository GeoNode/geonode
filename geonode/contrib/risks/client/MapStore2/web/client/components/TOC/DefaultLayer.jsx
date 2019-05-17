/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var Node = require('./Node');
var VisibilityCheck = require('./fragments/VisibilityCheck');
var Title = require('./fragments/Title');
var InlineSpinner = require('../misc/spinners/InlineSpinner/InlineSpinner');
var WMSLegend = require('./fragments/WMSLegend');
const ConfirmModal = require('../maps/modals/ConfirmModal');
const LayersTool = require('./fragments/LayersTool');
const SettingsModal = require('./fragments/SettingsModal');
const Message = require('../I18N/Message');

var DefaultLayer = React.createClass({
    propTypes: {
        node: React.PropTypes.object,
        settings: React.PropTypes.object,
        propertiesChangeHandler: React.PropTypes.func,
        retrieveLayerData: React.PropTypes.func,
        onToggle: React.PropTypes.func,
        onToggleQuerypanel: React.PropTypes.func,
        onZoom: React.PropTypes.func,
        onSettings: React.PropTypes.func,
        style: React.PropTypes.object,
        sortableStyle: React.PropTypes.object,
        hideSettings: React.PropTypes.func,
        updateSettings: React.PropTypes.func,
        updateNode: React.PropTypes.func,
        removeNode: React.PropTypes.func,
        activateLegendTool: React.PropTypes.bool,
        activateRemoveLayer: React.PropTypes.bool,
        activateSettingsTool: React.PropTypes.bool,
        activateQueryTool: React.PropTypes.bool,
        activateZoomTool: React.PropTypes.bool,
        settingsText: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        opacityText: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        saveText: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        closeText: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        confirmDeleteText: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        confirmDeleteMessage: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        modalOptions: React.PropTypes.object,
        settingsOptions: React.PropTypes.object,
        visibilityCheckType: React.PropTypes.string,
        includeDeleteButtonInSettings: React.PropTypes.bool,
        groups: React.PropTypes.array
    },
    getDefaultProps() {
        return {
            style: {},
            sortableStyle: {},
            propertiesChangeHandler: () => {},
            onToggle: () => {},
            onZoom: () => {},
            onSettings: () => {},
            retrieveLayerData: () => {},
            onToggleQuerypanel: () => {},
            activateRemoveLayer: false,
            activateLegendTool: false,
            activateSettingsTool: false,
            activateQueryTool: false,
            activateZoomTool: false,
            includeDeleteButtonInSettings: false,
            modalOptions: {},
            settingsOptions: {},
            confirmDeleteText: <Message msgId="layerProperties.deleteLayer" />,
            confirmDeleteMessage: <Message msgId="layerProperties.deleteLayerMessage" />,
            visibilityCheckType: "glyph"
        };
    },
    onConfirmDelete() {
        this.props.removeNode(this.props.node.id, "layers");
        this.closeDeleteDialog();
    },
    getInitialState: function() {
        return {
          showDeleteDialog: false
        };
    },
    renderCollapsible() {
        let tools = [];
        if (this.props.activateRemoveLayer) {
            tools.push((<LayersTool
                        node={this.props.node}
                        key="removelayer"
                        className="clayer_removal_button"
                        onClick={this.displayDeleteDialog}
                        tooltip="toc.removeLayer"
                        glyph="1-close"
                        />));
        }
        tools.push(
            <LayersTool node={this.props.node} key="toolsettings"
                    tooltip="toc.editLayerProperties"
                    glyph="cog"
                    onClick={(node) => this.props.onSettings(node.id, "layers",
                        {opacity: parseFloat(node.opacity !== undefined ? node.opacity : 1)})}/>
        );
        if (this.props.settings && this.props.settings.node === this.props.node.id) {
            tools.push(<SettingsModal
                            node={this.props.node}
                            key="toolsettingsmodal" options={this.props.modalOptions}
                           {...this.props.settingsOptions}
                           retrieveLayerData={this.props.retrieveLayerData}
                           hideSettings={this.props.hideSettings}
                           settings={this.props.settings}
                           element={this.props.node}
                           updateSettings={this.props.updateSettings}
                           updateNode={this.props.updateNode}
                           removeNode={this.props.removeNode}
                           includeDeleteButton={this.props.includeDeleteButtonInSettings}
                           titleText={this.props.settingsText}
                           opacityText={this.props.opacityText}
                           saveText={this.props.saveText}
                           closeText={this.props.closeText}
                           groups={this.props.groups}/>
               );
        }
        if (this.props.activateQueryTool && this.props.node.search) {
            tools.push(
                <LayersTool key="toolquery"
                        tooltip="toc.searchFeatures"
                        className="toc-queryTool"
                        node={this.props.node}
                        ref="target"
                        style={{"float": "right", cursor: "pointer"}}
                        glyph="search"
                        onClick={(node) => this.props.onToggleQuerypanel(node.search.url || node.url, node.name)}/>
                );
        }
        return (<div position="collapsible" className="collapsible-toc">
             <div style={{minHeight: "35px"}}>{tools}</div>
             <div><WMSLegend node={this.props.node}/></div>
        </div>);
    },
    renderTools() {
        const tools = [];
        if (this.props.visibilityCheckType) {
            tools.push(
                <VisibilityCheck key="visibilitycheck"
                   checkType={this.props.visibilityCheckType}
                   propertiesChangeHandler={this.props.propertiesChangeHandler}
                   style={{"float": "right", cursor: "pointer"}}/>
            );
        }
        if (this.props.activateLegendTool) {
            tools.push(
                <LayersTool
                        tooltip="toc.displayLegendAndTools"
                        key="toollegend"
                        className="toc-legendTool"
                        ref="target"
                        style={{"float": "right", cursor: "pointer"}}
                        glyph="1-menu-manage"
                        onClick={(node) => this.props.onToggle(node.id, node.expanded)}/>
                );
        }
        if (this.props.activateZoomTool && this.props.node.bbox && !this.props.node.loadingError) {
            tools.push(
                <LayersTool key="toolzoom"
                        tooltip="toc.zoomToLayerExtent"
                        className="toc-zoomTool"
                        ref="target"
                        style={{"float": "right", cursor: "pointer"}}
                        glyph="1-full-screen"
                        onClick={(node) => this.props.onZoom(node.bbox.bounds, node.bbox.crs)}/>
                );
        }
        return tools;
    },
    render() {
        let {children, propertiesChangeHandler, onToggle, ...other } = this.props;
        return (
            <Node className="toc-default-layer" sortableStyle={this.props.sortableStyle} style={this.props.style} type="layer" {...other}>
                <Title onClick={this.props.onToggle}/>
                <LayersTool key="loadingerror"
                        style={{"display": this.props.node.loadingError ? "block" : "none", color: "red", cursor: "default"}}
                        glyph="ban-circle"
                        tooltip="toc.loadingerror"
                        />
                {this.renderCollapsible()}
                {this.renderTools()}
                <InlineSpinner loading={this.props.node.loading}/>
                <ConfirmModal ref="removelayer" className="clayer_removal_confirm_button" show= {this.state.showDeleteDialog} onHide={this.closeDeleteDialog} onClose={this.closeDeleteDialog} onConfirm={this.onConfirmDelete} titleText={this.props.confirmDeleteText} confirmText={this.props.confirmDeleteText} cancelText={<Message msgId="cancel" />} body={this.props.confirmDeleteMessage} />
            </Node>
        );
    },
    closeDeleteDialog() {
        this.setState({
            showDeleteDialog: false
        });
    },
    displayDeleteDialog() {
        this.setState({
            showDeleteDialog: true
        });
    }
});

module.exports = DefaultLayer;
