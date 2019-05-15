/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var BootstrapReact = require('react-bootstrap');
var Modal = BootstrapReact.Modal;
var Button = BootstrapReact.Button;
var Glyphicon = BootstrapReact.Glyphicon;
var ImageButton = require('./ImageButton');
const Dialog = require('../misc/Dialog');
require('./css/infoButton.css');
const assign = require('object-assign');
/**
 * A button to show a simple information window.
 * Component's properies:
 *  - id: {string}            custom identifier for this component
 *  - title: {string|element} title of the window shown in its header
 *  - body: {string|element}  content of the window
 *  - style: {object}         a css-like hash to define the style on the component
 *  - glyphicon: {string}     bootstrap glyphicon name
 *  - text: {string|element}  text content for the button
 *  - btnSize: {string}       bootstrap button size ('large', 'small', 'xsmall')
 *  - btnType: {string}       'normal' to use a standard bootstrap button;
 *                            'image'  to use a custom image as button
 *
 * Note: the button will not be never empty, it will show at least the text (default or custom)
 */
const InfoButton = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        image: React.PropTypes.string,
        title: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        body: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        style: React.PropTypes.object,
        className: React.PropTypes.string,
        glyphicon: React.PropTypes.string,
        text: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        help: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        hiddenText: React.PropTypes.bool,
        btnSize: React.PropTypes.oneOf(['large', 'medium', 'small', 'xsmall']),
        btnType: React.PropTypes.oneOf(['normal', 'image']),
        modalOptions: React.PropTypes.object,
        useModal: React.PropTypes.bool,
        closeGlyph: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            id: "mapstore-infobutton",
            title: "Info",
            body: "",
            style: undefined,
            glyphicon: undefined,
            text: "Info",
            hiddenText: false,
            btnSize: 'medium',
            btnType: 'normal',
            modalOptions: {},
            useModal: true,
            closeGlyph: ""
        };
    },
    getInitialState() {
        return {
            isVisible: false
        };
    },
    getButton() {
        var btn;
        if (this.props.btnType === 'normal') {
            btn = (<Button
                    bsStyle="info"
                    bsSize={this.props.btnSize}
                    onClick={this.open}>
                    {this.props.glyphicon ? <Glyphicon glyph={this.props.glyphicon}/> : ""}
                    {!this.props.hiddenText && this.props.glyphicon ? "\u00A0" : ""}
                    {!(this.props.hiddenText && this.props.glyphicon) ? (this.props.text || this.props.help) : ""}
                </Button>);
        } else {
            btn = (<ImageButton image={this.props.image} onClick={this.open}/>);
        }
        return btn;
    },
    render() {
        const dialog = this.props.useModal ? (<Modal
            {...this.props.modalOptions}
            show={this.state.isVisible}
            onHide={this.close}
            bsStyle="info">
            <Modal.Header closeButton>
                <Modal.Title>{this.props.title}</Modal.Title>
            </Modal.Header>
            <Modal.Body>{this.props.body}</Modal.Body>
        </Modal>) : (
            <Dialog id="mapstore-about" style={assign({}, this.props.style, {display: this.state.isVisible ? "block" : "none"})}>
                <span role="header"><span className="about-panel-title">{this.props.title}</span><button onClick={this.close} className="about-panel-close close">{this.props.closeGlyph ? <Glyphicon glyph={this.props.closeGlyph}/> : <span>×</span>}</button></span>
                <div role="body">{this.props.body}</div>
            </Dialog>
        );
        return (
            <div
                id={this.props.id}
                style={this.props.style}
                className={this.props.className}>
                {this.getButton()}
                {dialog}
            </div>
        );
    },
    close() {
        this.setState({
            isVisible: false
        });
    },
    open() {
        this.setState({
            isVisible: true
        });
    }
});

module.exports = InfoButton;
