/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const LoginForm = require('../forms/LoginForm');
const {Modal, Button, Glyphicon} = require('react-bootstrap');
const Message = require('../../../components/I18N/Message');
const Dialog = require('../../misc/Dialog');
const LocaleUtils = require('../../../utils/LocaleUtils');

require('../css/security.css');
const assign = require('object-assign');

  /**
   * A Modal window to show password reset form
   */
const LoginModal = React.createClass({
  propTypes: {
      // props
      user: React.PropTypes.object,
      loginError: React.PropTypes.object,
      show: React.PropTypes.bool,
      options: React.PropTypes.object,

      // CALLBACKS
      onLoginSuccess: React.PropTypes.func,
      onSubmit: React.PropTypes.func,
      onError: React.PropTypes.func,
      onClose: React.PropTypes.func,
      useModal: React.PropTypes.bool,
      closeGlyph: React.PropTypes.string,
      style: React.PropTypes.object,
      buttonSize: React.PropTypes.string,
      includeCloseButton: React.PropTypes.bool
  },
  contextTypes: {
      messages: React.PropTypes.object
  },
  getDefaultProps() {
      return {
          onLoginSuccess: () => {},
          onSubmit: () => {},
          onError: () => {},
          onClose: () => {},
          options: {},
          useModal: true,
          closeGlyph: "",
          style: {},
          buttonSize: "large",
          includeCloseButton: true
      };
  },
  getForm() {
      return (<LoginForm
          role="body"
          ref="loginForm"
          showSubmitButton={false}
          user={this.props.user}
          loginError={this.props.loginError}
          onLoginSuccess={this.props.onLoginSuccess}
          onSubmit={this.props.onSubmit}
          onError={this.props.onError}
    />);
  },
  getFooter() {
      return (<span role="footer">
          <Button
              ref="submit"
              value={LocaleUtils.getMessageById(this.context.messages, "user.signIn")}
              bsStyle="primary"
              bsSize={this.props.buttonSize}
              className="pull-left"
              onClick={this.loginSubmit}
              key="submit">{LocaleUtils.getMessageById(this.context.messages, "user.signIn")}</Button>
          {this.props.includeCloseButton ? <Button
            key="closeButton"
            ref="closeButton"
            bsSize={this.props.buttonSize}
            onClick={this.props.onClose}><Message msgId="close"/></Button> : <span/>}
      </span>);
  },
  renderModal() {
      return (<Modal {...this.props.options} show={this.props.show} onHide={this.props.onClose}>
          <Modal.Header key="passwordChange" closeButton>
            <Modal.Title><Message msgId="user.login"/></Modal.Title>
          </Modal.Header>
          <Modal.Body>
              {this.getForm()}
          </Modal.Body>
          <Modal.Footer>
              {this.getFooter()}
          </Modal.Footer>
      </Modal>);
  },
  renderDialog() {
      return (this.props.show) ? (<Dialog modal id="mapstore-login-panel" style={assign({}, this.props.style, {display: "block" })}>
         <span role="header"><span className="login-panel-title"><Message msgId="user.login"/></span><button onClick={this.props.onClose} className="login-panel-close close">{this.props.closeGlyph ? <Glyphicon glyph={this.props.closeGlyph}/> : <span>×</span>}</button></span>
           {this.getForm()}
           {this.getFooter()}
     </Dialog>) : null;
  },
  render() {
      return this.props.useModal ? this.renderModal() : this.renderDialog();
  },
  loginSubmit() {
      this.refs.loginForm.submit();
  }
});

module.exports = LoginModal;
