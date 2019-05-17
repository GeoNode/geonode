/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {Modal, Button, Table, Alert, Glyphicon} = require('react-bootstrap');
const Dialog = require('../../../components/misc/Dialog');
const assign = require('object-assign');
const SecurityUtils = require('../../../utils/SecurityUtils');
const Message = require('../../../components/I18N/Message');

  /**
   * A Modal window to show password reset form
   */
const UserDetails = React.createClass({
  propTypes: {
      // props
      user: React.PropTypes.object,
      show: React.PropTypes.bool,
      displayAttributes: React.PropTypes.func,
      options: React.PropTypes.object,
      onClose: React.PropTypes.func,
      useModal: React.PropTypes.bool,
      closeGlyph: React.PropTypes.string,
      style: React.PropTypes.object,
      buttonSize: React.PropTypes.string,
      includeCloseButton: React.PropTypes.bool
  },
  getDefaultProps() {
      return {
          user: {
              name: "Guest"
          },
          displayAttributes: (attr) => {
              return attr.name !== "UUID";
          },
          onClose: () => {},
          options: {},
          useModal: true,
          closeGlyph: "",
          style: {},
          buttonSize: "large",
          includeCloseButton: true
      };
  },
  renderAttributes() {
      if (this.props.user && this.props.user.attribute) {
          let userAttributes = SecurityUtils.getUserAttributes(this.props.user);
          let attrsRendered = userAttributes.filter(this.props.displayAttributes).map((attr) => {
              return (<tr key={attr.name + "-row"}><th>{attr.name}</th><td> {attr.value}</td></tr>);
          });
          if (attrsRendered && attrsRendered.length > 0) {
              return <Table role="body" responsive striped condensed hover><tbody>{attrsRendered}</tbody></Table>;
          }
      }
      return <Alert type="info"><Message msgId="user.noAttributesMessage" /></Alert>;
  },
  getFooter() {
      return (this.props.includeCloseButton ? <Button bsSize={this.props.buttonSize} bsSize="small" onClick={this.props.onClose}><Message msgId="close"/></Button> : <span/>);
  },
  renderModal() {
      return (<Modal {...this.props.options} show={this.props.show} onHide={this.props.onClose}>
              <Modal.Header key="details" closeButton>
                <Modal.Title><Message msgId="user.details" /></Modal.Title>
              </Modal.Header>
              <Modal.Body>
                  {this.renderAttributes()}
              </Modal.Body>
              <Modal.Footer>
                {this.getFooter()}
              </Modal.Footer>
          </Modal>);
  },
  renderDialog() {
      return (this.props.show) ? (<Dialog id="mapstore-user-panel" modal style={assign({}, this.props.style, {display: "block"})}>
                  <span role="header"><span className="user-panel-title"><Message msgId="user.details" /></span><button onClick={this.props.onClose} className="login-panel-close close">{this.props.closeGlyph ? <Glyphicon glyph={this.props.closeGlyph}/> : <span>×</span>}</button></span>
                  {this.renderAttributes()}
                  {this.getFooter()}
              </Dialog>) : null;
  },
  render() {
      return this.props.useModal ? this.renderModal() : this.renderDialog();
  }

});

module.exports = UserDetails;
