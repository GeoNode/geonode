/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
 /**
  * Copyright 2016, GeoSolutions Sas.
  * All rights reserved.
  *
  * This source code is licensed under the BSD-style license found in the
  * LICENSE file in the root directory of this source tree.
  */

const React = require('react');

const {Button, Glyphicon} = require('react-bootstrap');

const Dialog = require('./Dialog');
const assign = require('object-assign');
const Message = require('../I18N/Message');
  /**
   * A Modal window to show password reset form
   */
const UserDialog = React.createClass({
  propTypes: {
      // props
      show: React.PropTypes.bool,
      onClose: React.PropTypes.func,
      onConfirm: React.PropTypes.func,
      onSave: React.PropTypes.func,
      modal: React.PropTypes.bool,
      closeGlyph: React.PropTypes.string,
      style: React.PropTypes.object,
      buttonSize: React.PropTypes.string,
      inputStyle: React.PropTypes.object,
      title: React.PropTypes.node,
      confirmButtonContent: React.PropTypes.node,
      confirmButtonDisabled: React.PropTypes.bool,
      closeText: React.PropTypes.node,
      confirmButtonBSStyle: React.PropTypes.string
  },
  getDefaultProps() {
      return {
          onClose: () => {},
          onChange: () => {},
          modal: true,
          title: <Message msgId="confirmTitle" />,
          closeGlyph: "",
          confirmButtonBSStyle: "danger",
          confirmButtonDisabled: false,
          confirmButtonContent: <Message msgId="confirm" /> || "Confirm",
          closeText: <Message msgId="close" />,
          includeCloseButton: true
      };
  },
  render() {
      return (<Dialog onClickOut={this.props.onClose} id="confirm-dialog" modal={this.props.modal} style={assign({}, this.props.style, {display: this.props.show ? "block" : "none"})}>
          <span role="header">
              <span className="user-panel-title">{this.props.title}</span>
              <button onClick={this.props.onClose} className="login-panel-close close">
                  {this.props.closeGlyph ? <Glyphicon glyph={this.props.closeGlyph}/> : <span>×</span>}
              </button>
          </span>
          <div role="body">
              {this.props.children}
          </div>
          <div role="footer">
              <Button onClick={this.props.onConfirm} disabled={this.props.confirmButtonDisabled}
                  bsStyle={this.props.confirmButtonBSStyle}>{this.props.confirmButtonContent}
              </Button>
              <Button onClick={this.props.onClose}>{this.props.closeText}</Button>
          </div>
      </Dialog>);
  }

});

module.exports = UserDialog;
