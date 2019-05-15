/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');

const {Modal, Button, Glyphicon} = require('react-bootstrap');

const Dialog = require('../../../components/misc/Dialog');
const assign = require('object-assign');


  /**
   * A Modal window to show a confirmation dialog
   */
const ConfirmModal = React.createClass({
    propTypes: {
        // props
        className: React.PropTypes.string,
        show: React.PropTypes.bool,
        options: React.PropTypes.object,
        onConfirm: React.PropTypes.func,
        onClose: React.PropTypes.func,
        useModal: React.PropTypes.bool,
        closeGlyph: React.PropTypes.string,
        style: React.PropTypes.object,
        buttonSize: React.PropTypes.string,
        includeCloseButton: React.PropTypes.bool,
        body: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        titleText: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        confirmText: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        cancelText: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element])
    },
    getDefaultProps() {
        return {
            onConfirm: ()=> {},
            onClose: () => {},
            options: {
                animation: false
            },
            className: "",
            useModal: true,
            closeGlyph: "",
            style: {},
            includeCloseButton: true,
            body: "",
            titleText: "Confirm Delete",
            confirmText: "Delete",
            cancelText: "Cancel"
        };
    },
    onConfirm() {
        this.props.onConfirm();
    },
    render() {
        const footer = (<span role="footer"><div style={{"float": "left"}}></div>
        <Button
            ref="confirmButton"
            className={this.props.className}
            key="confirmButton"
            bsStyle="primary"
            bsSize={this.props.buttonSize}
            onClick={() => {
                this.onConfirm();
            }}>{this.props.confirmText}</Button>
        {this.props.includeCloseButton ? <Button
            key="cancelButton"
            ref="cancelButton"
            bsSize={this.props.buttonSize}
            onClick={this.props.onClose}>{this.props.cancelText}</Button> : <span/>}
        </span>);
        const body = this.props.body;
        return this.props.useModal ? (
            <Modal {...this.props.options}
                show={this.props.show}
                onHide={this.props.onClose}>
                <Modal.Header key="dialogHeader" closeButton>
                  <Modal.Title>{this.props.titleText}</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {body}
                </Modal.Body>
                <Modal.Footer>
                  {footer}
                </Modal.Footer>
            </Modal>) : (
            <Dialog id="mapstore-confirmdialog-panel" style={assign({}, this.props.style, {display: this.props.show ? "block" : "none"})}>
                <span role="header"><span className="confirmdialog-panel-title">{this.props.titleText}</span><button onClick={this.props.onClose} className="confirmdialog-panel-close close">{this.props.closeGlyph ? <Glyphicon glyph={this.props.closeGlyph}/> : <span>×</span>}</button></span>
                {body}
                {footer}
            </Dialog>
        );
    }
});

module.exports = ConfirmModal;
