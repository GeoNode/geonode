/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const Metadata = require('../forms/Metadata');
const Thumbnail = require('../forms/Thumbnail');
const PermissionEditor = require('../../security/PermissionEditor');

require('./css/modals.css');

const {Modal, Button, Glyphicon, Grid, Row, Col} = require('react-bootstrap');
const Message = require('../../I18N/Message');

const Dialog = require('../../../components/misc/Dialog');
const assign = require('object-assign');

const Spinner = require('react-spinkit');
const LocaleUtils = require('../../../utils/LocaleUtils');

/**
* A Modal window to show map metadata form
*/
const MetadataModal = React.createClass({
    propTypes: {
        // props
        id: React.PropTypes.string,
        user: React.PropTypes.object,
        authHeader: React.PropTypes.string,
        show: React.PropTypes.bool,
        options: React.PropTypes.object,
        loadPermissions: React.PropTypes.func,
        loadAvailableGroups: React.PropTypes.func,
        onSave: React.PropTypes.func,
        onCreateThumbnail: React.PropTypes.func,
        onDeleteThumbnail: React.PropTypes.func,
        onGroupsChange: React.PropTypes.func,
        onAddPermission: React.PropTypes.func,
        onClose: React.PropTypes.func,
        useModal: React.PropTypes.bool,
        closeGlyph: React.PropTypes.string,
        buttonSize: React.PropTypes.string,
        includeCloseButton: React.PropTypes.bool,
        map: React.PropTypes.object,
        style: React.PropTypes.object,
        fluid: React.PropTypes.bool,
        // I18N
        errorImage: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        errorMessages: React.PropTypes.object,
        // CALLBACKS
        onSaveAll: React.PropTypes.func,
        onRemoveThumbnail: React.PropTypes.func,
        onErrorCurrentMap: React.PropTypes.func,
        onUpdateCurrentMap: React.PropTypes.func,
        onNewGroupChoose: React.PropTypes.func,
        onNewPermissionChoose: React.PropTypes.func,
        displayPermissionEditor: React.PropTypes.bool,
        availablePermissions: React.PropTypes.arrayOf(React.PropTypes.string),
        availableGroups: React.PropTypes.arrayOf(React.PropTypes.object),
        updatePermissions: React.PropTypes.func,
        groups: React.PropTypes.arrayOf(React.PropTypes.object),
        newGroup: React.PropTypes.object,
        newPermission: React.PropTypes.string
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getInitialState() {
        return {
            name: this.props.map && this.props.map.name || '',
            description: this.props.map && this.props.map.description || ''
        };
    },
    getDefaultProps() {
        return {
            id: "MetadataModal",
            loadPermissions: () => {},
            loadAvailableGroups: () => {},
            onSave: ()=> {},
            onCreateThumbnail: ()=> {},
            onDeleteThumbnail: ()=> {},
            onGroupsChange: ()=> {},
            onAddPermission: ()=> {},
            onNewGroupChoose: ()=> {},
            onNewPermissionChoose: ()=> {},
            user: {
                name: "Guest"
            },
            options: {},
            useModal: true,
            closeGlyph: "",
            style: {},
            buttonSize: "small",
            includeCloseButton: true,
            fluid: true,
            // CALLBACKS
            onErrorCurrentMap: ()=> {},
            onUpdateCurrentMap: ()=> {},
            onSaveAll: () => {},
            onRemoveThumbnail: ()=> {},
            onSaveMap: ()=> {},
            onClose: () => {},
            // I18N
            errorMessages: {"FORMAT": <Message msgId="map.errorFormat"/>, "SIZE": <Message msgId="map.errorSize"/>},
            errorImage: <Message msgId="map.error"/>,
            displayPermissionEditor: true,
            availablePermissions: ["canRead", "canWrite"],
            availableGroups: [],
            updatePermissions: () => {},
            groups: []
        };
    },
    componentWillMount() {
        if (this.props.map && this.props.map.name) {
            this.setState({
                name: this.props.map.name,
                description: this.props.map.description || ''
            });
        }
    },
    componentWillReceiveProps(nextProps) {
        if (nextProps.map && this.props.map && !nextProps.map.loading && this.state && this.state.saving) {
            this.setState({
              saving: false
            });
            this.props.onClose();
        }
        if (nextProps.map && nextProps.map.name) {
            this.setState({
                name: nextProps.map.name,
                description: nextProps.map.description || ''
            });
        }
    },
    componentDidUpdate(prevProps) {
        if (this.props.show && !prevProps.show) {
            if (this.props.displayPermissionEditor && (this.props.user.name === this.props.map.owner || this.props.user.role === "ADMIN" )) {
                this.loadPermissions();
                this.loadAvailableGroups();
            }
        }
    },
    updateThumbnail() {
        this.refs.thumbnail.updateThumbnail();
    },
    loadPermissions() {
        this.props.loadPermissions(this.props.map.id);
    },
    loadAvailableGroups() {
        this.props.loadAvailableGroups(this.props.user);
    },
    onSave() {
        this.setState({
            saving: true
        });
        let metadata = null;

        if ( this.isMetadataChanged() ) {
            let name = this.state.name;
            let description = this.state.description;
            metadata = {
                name: name,
                description: description
            };
            this.props.onSave(this.props.map.id, name, description);
        }
        this.props.updatePermissions(this.props.map.id, this.props.map.permissions);
        this.refs.thumbnail.updateThumbnail(this.props.map, metadata);
    },
    renderPermissionEditor() {
        if (this.props.displayPermissionEditor && this.props.user.name === this.props.map.owner || this.props.user.role === "ADMIN" ) {
            // Hack to convert map permissions to a simpler format, TODO: remove this
            if (this.props.map && this.props.map.permissions && this.props.map.permissions.SecurityRuleList && this.props.map.permissions.SecurityRuleList.SecurityRule) {
                this.localGroups = this.props.map.permissions.SecurityRuleList.SecurityRule.map(function(rule) {
                        if (rule && rule.group && rule.canRead) {
                            return {name: rule.group.groupName, permission: rule.canWrite ? "canWrite" : "canRead" };
                        }
                    }
                ).filter(rule => rule);  // filter out undefined values
            } else {
                this.localGroups = this.props.groups;
            }
            return (
                <PermissionEditor
                    map={this.props.map}
                    user={this.props.user}
                    availablePermissions ={this.props.availablePermissions}
                    availableGroups={this.props.availableGroups}
                    groups={this.props.groups}
                    newGroup={this.props.newGroup}
                    newPermission={this.props.newPermission}
                    onNewGroupChoose={this.props.onNewGroupChoose}
                    onNewPermissionChoose={this.props.onNewPermissionChoose}
                    onAddPermission={this.props.onAddPermission}
                    onGroupsChange={this.props.onGroupsChange}
                />
            );
        }
    },
    renderLoading() {
        return this.props.map && this.props.map.updating ? <Spinner spinnerName="circle" key="loadingSpinner" noFadeIn overrideSpinnerClassName="spinner"/> : null;
    },
    render() {
        const footer = (<span role="footer"><div style={{"float": "left"}}>{this.renderLoading()}</div>
            <Button
                ref="metadataSaveButton"
                key="metadataSaveButton"
                bsStyle="primary"
                bsSize={this.props.buttonSize}
                onClick={() => {
                    this.onSave();
                }}><Message msgId="save" /></Button>
            {this.props.includeCloseButton ? <Button
                key="closeButton"
                ref="closeButton"
                bsSize={this.props.buttonSize}
                onClick={this.props.onClose}><Message msgId="close" /></Button> : <span/>}
            </span>);
        const body = (
            <Metadata role="body" ref="mapMetadataForm"
                onChange={(prop, value ) => {
                    this.setState({
                        [prop]: value
                    });
                }}
                map={this.props.map}
                nameFieldText={<Message msgId="map.name" />}
                descriptionFieldText={<Message msgId="map.description" />}
                namePlaceholderText={LocaleUtils.getMessageById(this.context.messages, "map.namePlaceholder") || "Map Name"}
                descriptionPlaceholderText={LocaleUtils.getMessageById(this.context.messages, "map.descriptionPlaceholder") || "Map Description"}
            />);
        const mapErrorStatus = (this.props.map && this.props.map.mapError && this.props.map.mapError.status ? this.props.map.mapError.status : null);
        let messageIdMapError = "";
        if (mapErrorStatus === 404 || mapErrorStatus === 403 || mapErrorStatus === 409) {
            messageIdMapError = mapErrorStatus;
        } else {
            messageIdMapError = "Default";
        }
        const thumbnailErrorStatus = (this.props.map && this.props.map.thumbnailError && this.props.map.thumbnailError.status ? this.props.map.thumbnailError.status : null);
        let messageIdError = "";
        if (thumbnailErrorStatus === 404 || thumbnailErrorStatus === 403 || thumbnailErrorStatus === 409) {
            messageIdError = thumbnailErrorStatus;
        } else {
            messageIdError = "Default";
        }
        return this.props.useModal ? (
            <Modal {...this.props.options}
                show={this.props.show}
                onHide={this.props.onClose}
                id={this.props.id}>
                <Modal.Header key="mapMetadata" closeButton>
                    <Modal.Title>
                        <Message msgId="manager.editMapMetadata" />
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Grid fluid={this.props.fluid}>
                        <Row>
                            {(this.props.map && this.props.map.mapError) ?
                                (<div className="dropzone-errorBox alert-danger">
                                    <div id={"error" + messageIdMapError} key={"error" + messageIdMapError} className={"error" + messageIdMapError}>
                                        <Message msgId={"map.mapError.error" + messageIdMapError}/>
                                    </div>
                                </div>)
                            : null }
                            {(this.props.map && this.props.map.errors && this.props.map.errors.length > 0 ) ?
                            (<div className="dropzone-errorBox alert-danger">
                                <p>{this.props.errorImage}</p>
                                { (this.props.map.errors.map((error) => <div id={"error" + error} key={"error" + error} className={"error" + error}> {this.props.errorMessages[error]} </div>))}
                            </div>)
                            : null }
                            {(this.props.map && this.props.map.thumbnailError) ?
                                (<div className="dropzone-errorBox alert-danger">
                                    <div id={"error" + messageIdError} key={"error" + messageIdError} className={"error" + messageIdError}>
                                        <Message msgId={"map.thumbnailError.error" + messageIdError}/>
                                    </div>
                                </div>)
                            : null }
                        </Row>
                        <Row>
                            <Col xs={7}>
                                <Thumbnail
                                    map={this.props.map}
                                    onSaveAll={this.props.onSaveAll}
                                    onRemoveThumbnail={this.props.onRemoveThumbnail}
                                    onError={this.props.onErrorCurrentMap}
                                    onUpdate={this.props.onUpdateCurrentMap}
                                    onCreateThumbnail={this.props.onCreateThumbnail}
                                    onDeleteThumbnail={this.props.onDeleteThumbnail}
                                    ref="thumbnail"/>
                            </Col>
                            <Col xs={5}>
                                {body}
                            </Col>
                        </Row>
                        {this.renderPermissionEditor()}
                    </Grid>
                </Modal.Body>
                <Modal.Footer>
                  {footer}
                </Modal.Footer>
            </Modal>) : (
            <Dialog id="mapstore-mapmetadata-panel" style={assign({}, this.props.style, {display: this.props.show ? "block" : "none"})}>
                <span role="header"><span className="mapmetadata-panel-title"><Message msgId="manager.editMapMetadata" /></span><button onClick={this.props.onClose} className="login-panel-close close">{this.props.closeGlyph ? <Glyphicon glyph={this.props.closeGlyph}/> : <span>×</span>}</button></span>
                {body}
                {footer}
            </Dialog>
        );
    },
    isMetadataChanged() {
        return this.props.map && (
            this.state.description !== this.props.map.description ||
            this.state.name !== this.props.map.name
        );
    },
    isThumbnailChanged() {
        return this.refs && this.refs.thumbnail && this.refs.thumbnail.files && this.refs.thumbnail.files.length > 0;
    }
});

module.exports = MetadataModal;
