/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Modal, Button, Glyphicon, Tabs, Tab} = require('react-bootstrap');

require("./css/settingsModal.css");

const Dialog = require('../../misc/Dialog');
const ConfirmButton = require('../../buttons/ConfirmButton');
const General = require('./settings/General');
const Display = require('./settings/Display');
const WMSStyle = require('./settings/WMSStyle');
const {Portal} = require('react-overlays');
const assign = require('object-assign');
const Message = require('../../I18N/Message');

const SettingsModal = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        settings: React.PropTypes.object,
        element: React.PropTypes.object,
        updateSettings: React.PropTypes.func,
        hideSettings: React.PropTypes.func,
        updateNode: React.PropTypes.func,
        removeNode: React.PropTypes.func,
        retrieveLayerData: React.PropTypes.func,
        titleText: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        opacityText: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        saveText: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        deleteText: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        confirmDeleteText: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        closeText: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        options: React.PropTypes.object,
        asModal: React.PropTypes.bool,
        buttonSize: React.PropTypes.string,
        closeGlyph: React.PropTypes.string,
        panelStyle: React.PropTypes.object,
        panelClassName: React.PropTypes.string,
        includeCloseButton: React.PropTypes.bool,
        includeDeleteButton: React.PropTypes.bool,
        realtimeUpdate: React.PropTypes.bool,
        groups: React.PropTypes.array
    },
    getDefaultProps() {
        return {
            id: "mapstore-layer-settings",
            settings: {expanded: false},
            options: {},
            updateSettings: () => {},
            hideSettings: () => {},
            updateNode: () => {},
            removeNode: () => {},
            retrieveLayerData: () => {},
            asModal: true,
            buttonSize: "large",
            closeGlyph: "",
            panelStyle: {
                minWidth: "300px",
                zIndex: 2000,
                position: "absolute",
                // overflow: "auto",
                top: "100px",
                left: "calc(50% - 150px)"
            },
            panelClassName: "toolbar-panel",
            includeCloseButton: true,
            includeDeleteButton: true,
            realtimeUpdate: true,
            deleteText: <Message msgId="layerProperties.delete" />,
            confirmDeleteText: <Message msgId="layerProperties.confirmDelete" />
        };
    },
    getInitialState() {
        return {
            initialState: {},
            originalSettings: {}
        };
    },
    componentWillMount() {
        this.setState({initialState: this.props.element});
    },
    onDelete() {
        this.props.removeNode(
            this.props.settings.node,
            this.props.settings.nodeType
        );
        this.props.hideSettings();
    },
    onClose() {
        this.props.updateNode(
            this.props.settings.node,
            this.props.settings.nodeType,
            assign({}, this.props.settings.options, this.state.originalSettings)
        );
        this.props.hideSettings();
    },
    renderGeneral() {
        return (<General
            updateSettings={this.updateParams}
            element={this.props.element}
            groups={this.props.groups}
            key="general"
            on/>);
    },
    renderDisplay() {
        return (<Display
           opacityText={this.props.opacityText}
           element={this.props.element}
           settings={this.props.settings}
           onChange={(key, value) => this.updateParams({[key]: value}, this.props.realtimeUpdate)} />);
    },
    renderStyleTab() {
        if (this.props.element.type === "wms") {
            return (<WMSStyle
                    retrieveLayerData={this.props.retrieveLayerData}
                    updateSettings={this.updateParams}
                    element={this.props.element}
                    key="style"
                    o/>);
        }
    },
    render() {
        const general = this.renderGeneral();
        const display = this.renderDisplay();
        const style = this.renderStyleTab();
        const tabs = (<Tabs defaultActiveKey={1} id="layerProperties-tabs">
            <Tab eventKey={1} title={<Message msgId="layerProperties.general" />}>{general}</Tab>
            <Tab eventKey={2} title={<Message msgId="layerProperties.display" />}>{display}</Tab>
            <Tab eventKey={3} title={<Message msgId="layerProperties.style" />} disabled={!style} >{style}</Tab>
          </Tabs>);
        const footer = (<span role="footer">
            {this.props.includeCloseButton ? <Button bsSize={this.props.buttonSize} onClick={this.onClose}>{this.props.closeText}</Button> : <span/>}
            {this.props.includeDeleteButton ?
                <ConfirmButton
                  onConfirm={this.onDelete}
                  text={this.props.deleteText}
                  confirming={{
                      text: this.props.confirmDeleteText
                  }}
                />
            : <span/>}
            <Button bsSize={this.props.buttonSize} bsStyle="primary" onClick={() => {
                this.updateParams(this.props.settings.options.opacity, true);
                this.props.hideSettings();
            }}>{this.props.saveText}</Button>
        </span>);

        if (this.props.settings.expanded) {
            return this.props.asModal ? (
                <Modal {...this.props.options} show={this.props.settings.expanded} container={document.getElementById("body")}>
                    <Modal.Header><Modal.Title>{this.props.titleText}</Modal.Title></Modal.Header>
                    <Modal.Body>
                        {tabs}
                    </Modal.Body>
                    <Modal.Footer>
                        {footer}
                    </Modal.Footer>
                </Modal>
            ) : (<Portal><Dialog id={this.props.id} style={this.props.panelStyle} className={this.props.panelClassName}>
                <span role="header">
                    <span className="layer-settings-panel-title">{this.props.titleText}</span>
                    <button onClick={this.onClose} className="layer-settings-panel-close close">{this.props.closeGlyph ? <Glyphicon glyph={this.props.closeGlyph}/> : <span>×</span>}</button>
                </span>
                <div role="body">
                    {tabs}
                </div>
                {footer}
            </Dialog></Portal>);
        }
        return null;
    },
    updateParams(newParams, updateNode = true) {
        let originalSettings = assign({}, this.state.originalSettings);
        // TODO one level only storage of original settings for the moment
        Object.keys(newParams).forEach((key) => {
            originalSettings[key] = this.state.initialState[key];
        });
        this.setState({originalSettings});
        this.props.updateSettings(newParams);
        if (updateNode) {
            this.props.updateNode(
                this.props.settings.node,
                this.props.settings.nodeType,
                assign({}, this.props.settings.props, newParams)
            );
        }
    }
});

module.exports = SettingsModal;
