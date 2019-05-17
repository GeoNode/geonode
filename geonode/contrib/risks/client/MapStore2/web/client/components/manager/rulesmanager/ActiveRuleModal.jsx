/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Modal, Button, Alert} = require('react-bootstrap');

const Message = require('../../I18N/Message');
const RuleAttributes = require('./RuleAttributes');

const ActiveRuleModal = React.createClass({
    propTypes: {
        updateActiveRule: React.PropTypes.func,
        addRule: React.PropTypes.func,
        updateRule: React.PropTypes.func,
        loadRoles: React.PropTypes.func,
        loadUsers: React.PropTypes.func,
        loadWorkspaces: React.PropTypes.func,
        loadLayers: React.PropTypes.func,
        options: React.PropTypes.object,
        services: React.PropTypes.object,
        activeRule: React.PropTypes.object,
        error: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            updateActiveRule: () => {},
            addRule: () => {},
            updateRule: () => {},
            activeRule: {},
            error: {}
        };
    },
    onClose() {
        this.props.updateActiveRule({}, undefined, false);
    },
    getOnSubmitHandler(status) {
        if (status === "new") {
            return this.props.addRule;
        } else if (status === "edit") {
            return this.props.updateRule;
        }
    },
    getUpdateRuleAttributesHandler() {
        const status = this.props.activeRule.status;
        return function(updatedAttributes) {
            this.props.updateActiveRule(updatedAttributes, status, true);
        }.bind(this);
    },
    render() {
        const status = this.props.activeRule.status;
        const showModal = status === "edit" || status === "new";
        if (!showModal) {
            return null;
        }
        const titleMsgId = "rulesmanager." + status + "Modal";
        const buttonMsgId = "rulesmanager." + status + "Button";
        return (
            <Modal show={showModal} {...this.props} bsSize="small">
                <Modal.Header closeButton onHide={this.onClose}>
                    <Modal.Title>
                        <Message msgId={titleMsgId}/>
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <RuleAttributes
                        loadRoles={() => this.props.loadRoles("modal")}
                        loadUsers={this.props.loadUsers}
                        loadWorkspaces={this.props.loadWorkspaces}
                        loadLayers={this.props.loadLayers}
                        options={this.props.options}
                        services={this.props.services}
                        updateRuleAttributes={this.getUpdateRuleAttributesHandler()}
                        ruleAttributes={this.props.activeRule.rule}
                        showAccess={true}
                        containerClassName={"modal-rules"}
                        selectClassName={"modal-rules-select"}
                        context="modal"/>
                </Modal.Body>
                <Modal.Footer style={{textAlign: "center"}}>
                    <Button bsSize="small" bsStyle="primary" onClick={this.getOnSubmitHandler(status)}>
                        <Message msgId={buttonMsgId}/>
                    </Button>
                    <Button bsSize="small" bsStyle="primary" onClick={this.onClose}>
                        <Message msgId={"rulesmanager.close"}/>
                    </Button>
                    { this.props.error.context === "modal" &&
                        <Alert className="error-modal-panel" bsStyle="danger">
                            <Message msgId={this.props.error.msgId}/>
                        </Alert>
                    }
                </Modal.Footer>
            </Modal>
        );
    }
});

module.exports = ActiveRuleModal;
