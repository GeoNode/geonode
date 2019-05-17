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

const {Alert, Tabs, Tab, Button, Glyphicon, Checkbox, FormControl, FormGroup, ControlLabel} = require('react-bootstrap');

const Dialog = require('../../../components/misc/Dialog');
const UserGroups = require('./UserGroups');
const assign = require('object-assign');
const Message = require('../../../components/I18N/Message');
const Spinner = require('react-spinkit');
const {findIndex} = require('lodash');

require('./style/userdialog.css');
  /**
   * A Modal window to show password reset form
   */
const UserDialog = React.createClass({
  propTypes: {
      // props
      user: React.PropTypes.object,
      groups: React.PropTypes.array,
      groupsStatus: React.PropTypes.string,
      show: React.PropTypes.bool,
      onClose: React.PropTypes.func,
      onChange: React.PropTypes.func,
      onSave: React.PropTypes.func,
      modal: React.PropTypes.bool,
      closeGlyph: React.PropTypes.string,
      style: React.PropTypes.object,
      buttonSize: React.PropTypes.string,
      inputStyle: React.PropTypes.object,
      attributes: React.PropTypes.array
  },
  getDefaultProps() {
      return {
          user: {},
          onClose: () => {},
          onChange: () => {},
          onSave: () => {},
          options: {},
          useModal: true,
          closeGlyph: "",
          style: {},
          buttonSize: "large",
          includeCloseButton: true,
          attributes: [{
              name: "email"
          }, {
              name: "company"
          }, {
              name: "notes"
          }],
          inputStyle: {
              height: "32px",
              width: "260px",
              marginTop: "3px",
              marginBottom: "20px",
              padding: "5px",
              border: "1px solid #078AA3"
          }
      };
  },
  getAttributeValue(name) {
      let attrs = this.props.user && this.props.user.attribute;
      if (attrs) {
          let index = findIndex(attrs, a => a.name === name);
          return attrs[index] && attrs[index].value;
      }
  },
  getPwStyle() {
      if (!this.props.user || !this.props.user.newPassword) {
          return null;
      }
      let pw = this.props.user.newPassword;
      if (pw.length === 0) {
          return null;
      }
      return pw.length > 5 ? "success" : "warning";

  },
  renderGeneral() {
      return (<div style={{clear: "both"}}>
      <FormGroup>
          <ControlLabel><Message msgId="user.username"/></ControlLabel>
          <FormControl ref="name"
              key="name"
              type="text"
              name="name"
              readOnly={this.props.user && this.props.user.id}
              style={this.props.inputStyle}
              onChange={this.handleChange}
              value={this.props.user && this.props.user.name}/>
      </FormGroup>
      <FormGroup validationState={this.getPwStyle()}>
          <ControlLabel><Message msgId="user.password"/></ControlLabel>
          <FormControl ref="newPassword"
              key="newPassword"
              type="password"
              name="newPassword"
              autoComplete="new-password"
              style={this.props.inputStyle}
              onChange={this.handleChange} />
      </FormGroup>
      <FormGroup validationState={ (this.props.user && this.props.user.newPassword && (this.isValidPassword() ? "success" : "error")) || null}>
          <ControlLabel><Message msgId="user.retypePwd"/></ControlLabel>
          <FormControl ref="confirmPassword"
              key="confirmPassword"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              style={this.props.inputStyle}
              onChange={this.handleChange} />
      </FormGroup>
      <select name="role" style={this.props.inputStyle} onChange={this.handleChange} value={this.props.user && this.props.user.role}>
        <option value="ADMIN">ADMIN</option>
        <option value="USER">USER</option>
      </select>
      <FormGroup>
          <ControlLabel><Message msgId="users.enabled"/></ControlLabel>
          <Checkbox
              checked={this.props.user && (this.props.user.enabled === undefined ? false : this.props.user.enabled)}
              type="checkbox"
              key={"enabled" + (this.props.user ? this.props.user.enabled : "missing")}
              name="enabled"
              onClick={(evt) => {this.props.onChange("enabled", evt.target.checked ? true : false); }} />
      </FormGroup>
      </div>);
  },
  renderAttributes() {
      return this.props.attributes.map((attr) => {
          return (<FormGroup>
              <ControlLabel>{attr.name}</ControlLabel>
              <FormControl ref={"attribute." + attr.name}
              key={"attribute." + attr.name}
              name={"attribute." + attr.name}
              type="text"
              style={this.props.inputStyle}
              onChange={this.handleChange}
              value={this.getAttributeValue(attr.name)} /></FormGroup>);
      });
  },
  renderSaveButtonContent() {
      let status = this.props.user && this.props.user.status;
      let defaultMessage = this.props.user && this.props.user.id ? <Message key="text" msgId="users.saveUser"/> : <Message key="text" msgId="users.createUser" />;
      let messages = {
          error: defaultMessage,
          success: defaultMessage,
          modified: defaultMessage,
          save: <Message key="text" msgId="users.saveUser"/>,
          saving: <Message key="text" msgId="users.savingUser" />,
          saved: <Message key="text" msgId="users.userSaved" />,
          creating: <Message key="text" msgId="users.creatingUser" />,
          created: <Message key="text" msgId="users.userCreated" />
      };
      let message = messages[status] || defaultMessage;
      return [this.isSaving() ? <Spinner key="saving-spinner" spinnerName="circle" noFadeIn overrideSpinnerClassName="spinner"/> : null, message];
  },
  renderButtons() {
      return [
          <Button key="save" bsSize={this.props.buttonSize} bsSize="small"
              bsStyle={this.isSaved() ? "success" : "primary" }
              onClick={() => this.props.onSave(this.props.user)}
              disabled={!this.isValid() || this.isSaving()}>
              {this.renderSaveButtonContent()}</Button>,
          <Button key="close" bsSize={this.props.buttonSize} bsSize="small" onClick={this.props.onClose}><Message msgId="close"/></Button>

      ];
  },
  renderGroups() {
      return <UserGroups onUserGroupsChange={this.props.onChange} user={this.props.user} groups={this.props.groups} />;
  },
  renderError() {
      let error = this.props.user && this.props.user.status === "error";
      if ( error ) {
          let lastError = this.props.user && this.props.user.lastError;
          return <Alert key="error" bsStyle="warning"><Message msgId="users.errorSaving" />{lastError && lastError.statusText}</Alert>;
      }

  },
  render() {
      return (<Dialog onClickOut={this.props.onClose} modal={true} maskLoading={this.props.user && (this.props.user.status === "loading" || this.props.user.status === "saving")} id="mapstore-user-dialog" className="user-edit-dialog" style={assign({}, this.props.style, {display: this.props.show ? "block" : "none"})}>

          <span role="header">
              <span className="user-panel-title">{(this.props.user && this.props.user.name) || <Message msgId="users.newUser" />}</span>
              <button onClick={this.props.onClose} className="login-panel-close close">
                  {this.props.closeGlyph ? <Glyphicon glyph={this.props.closeGlyph}/> : <span>×</span>}
              </button>
          </span>
          <div role="body">
          <Tabs defaultActiveKey={1} key="tab-panel">
              <Tab eventKey={1} title={<Button className="square-button" bsSize={this.props.buttonSize} bsStyle="primary"><Glyphicon glyph="user"/></Button>} >
                  {this.renderGeneral()}
              </Tab>
              <Tab eventKey={2} title={<Button className="square-button" bsSize={this.props.buttonSize} bsStyle="primary"><Glyphicon glyph="info-sign"/></Button>} >
                  {this.renderAttributes()}
              </Tab>
              <Tab eventKey={3} title={<Button className="square-button" bsSize={this.props.buttonSize} bsStyle="primary"><Glyphicon glyph="1-group"/></Button>} >
                  {this.renderGroups()}
              </Tab>
          </Tabs>
          </div>
          <div role="footer">
              {this.renderError()}
              {this.renderButtons()}
          </div>
      </Dialog>);
  },
  isSaving() {
      return this.props.user && this.props.user.status === "saving";
  },
  isSaved() {
      return this.props.user && (this.props.user.status === "saved" || this.props.user.status === "created");
  },
  isValid() {
      let valid = true;
      let user = this.props.user;
      if (!user) return false;
      valid = valid && user.name && user.status === "modified" && this.isValidPassword();
      return valid;
  },
  isValidPassword() {
      let valid = true;
      let user = this.props.user;
      if (user && user.id) {
          if (user.newPassword) {
              valid = valid && (user.confirmPassword === user.newPassword);
          }
      } else {
          valid = valid && user && user.newPassword && (user.confirmPassword === user.newPassword);
      }
      return valid;
  },
  handleChange(event) {
      this.props.onChange(event.target.name, event.target.value);
  }

});

module.exports = UserDialog;
