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
const UsersTable = require('./UsersTable');
const {Alert, Tabs, Tab, Button, Glyphicon, FormControl, FormGroup, ControlLabel} = require('react-bootstrap');

const Dialog = require('../../../components/misc/Dialog');
const assign = require('object-assign');
const Message = require('../../../components/I18N/Message');
const Spinner = require('react-spinkit');
const Select = require("react-select");
const {findIndex} = require('lodash');

require('./style/userdialog.css');
  /**
   * A Modal window to show password reset form
   */
const GroupDialog = React.createClass({
  propTypes: {
      // props
      group: React.PropTypes.object,
      users: React.PropTypes.array,
      availableUsers: React.PropTypes.array,
      searchUsers: React.PropTypes.func,
      availableUsersLoading: React.PropTypes.bool,
      show: React.PropTypes.bool,
      onClose: React.PropTypes.func,
      onChange: React.PropTypes.func,
      onSave: React.PropTypes.func,
      modal: React.PropTypes.bool,
      closeGlyph: React.PropTypes.string,
      style: React.PropTypes.object,
      buttonSize: React.PropTypes.string,
      descLimit: React.PropTypes.number,
      nameLimit: React.PropTypes.number,
      inputStyle: React.PropTypes.object
  },
  getDefaultProps() {
      return {
          group: {},
          availableUsers: [],
          onClose: () => {},
          onChange: () => {},
          onSave: () => {},
          options: {},
          useModal: true,
          closeGlyph: "",
          descLimit: 255,
          nameLimit: 255,
          style: {},
          buttonSize: "large",
          includeCloseButton: true,
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
  getCurrentGroupMembers() {
      return this.props.group && (this.props.group.newUsers || this.props.group.users) || [];
  },
  renderGeneral() {
      return (<div style={{clear: "both"}}>
      <FormGroup>
          <ControlLabel><Message msgId="usergroups.groupName"/></ControlLabel>
          <FormControl ref="groupName"
              key="groupName"
              type="text"
              name="groupName"
              readOnly={this.props.group && this.props.group.id}
              style={this.props.inputStyle}
              onChange={this.handleChange}
              maxLength={this.props.nameLimit}
              value={this.props.group && this.props.group.groupName}/>
      </FormGroup>
      <FormGroup>
          <ControlLabel><Message msgId="usergroups.groupDescription"/></ControlLabel>
          <FormControl componentClass="textarea"
              ref="description"
              key="description"
              name="description"
              maxLength={this.props.descLimit}
              readOnly={this.props.group && this.props.group.id}
              style={this.props.inputStyle}
              onChange={this.handleChange}
              value={this.props.group && this.props.group.description || ""}/>
      </FormGroup>
      </div>);
  },

  renderSaveButtonContent() {
      let defaultMessage = this.props.group && this.props.group.id ? <Message key="text" msgId="usergroups.saveGroup"/> : <Message key="text" msgId="usergroups.createGroup" />;
      let messages = {
          error: defaultMessage,
          success: defaultMessage,
          modified: defaultMessage,
          save: <Message key="text" msgId="usergroups.saveGroup"/>,
          saving: <Message key="text" msgId="usergroups.savingGroup" />,
          saved: <Message key="text" msgId="usergroups.groupSaved" />,
          creating: <Message key="text" msgId="usergroups.creatingGroup" />,
          created: <Message key="text" msgId="usergroups.groupCreated" />
      };
      let message = messages[status] || defaultMessage;
      return [this.isSaving() ? <Spinner key="saving-spinner" spinnerName="circle" noFadeIn overrideSpinnerClassName="spinner"/> : null, message];
  },
  renderButtons() {
      return [
          <Button key="save" bsSize={this.props.buttonSize} bsSize="small"
              bsStyle={this.isSaved() ? "success" : "primary" }
              onClick={() => this.props.onSave(this.props.group)}
              disabled={!this.isValid() || this.isSaving()}>
              {this.renderSaveButtonContent()}</Button>,
          <Button key="close" bsSize={this.props.buttonSize} bsSize="small" onClick={this.props.onClose}><Message msgId="close"/></Button>

      ];
  },

  renderError() {
      let error = this.props.group && this.props.group.status === "error";
      if ( error ) {
          let lastError = this.props.group && this.props.group.lastError;
          return <Alert key="error" bsStyle="warning"><Message msgId="usergroups.errorSaving" />{lastError && lastError.statusText}</Alert>;
      }

  },
  renderMembers() {
      let members = this.getCurrentGroupMembers();
      if (!members || members.length === 0) {
          return (<div style={{
                  width: "100%",
                  textAlign: "center"
              }}><Message msgId="usergroups.noUsers"/></div>);
      }
      // NOTE: faking group Id
      return (<UsersTable users={[...members].sort((u1, u2) => u1.name > u2.name)} onRemove={(user) => {
          let id = user.id;
          let newUsers = this.getCurrentGroupMembers().filter(u => u.id !== id);
          this.props.onChange("newUsers", newUsers);
      }}/>);
  },
  renderMembersTab() {
      let availableUsers = this.props.availableUsers.filter((user) => findIndex(this.getCurrentGroupMembers(), member => member.id === user.id) < 0).map(u => ({value: u.id, label: u.name}));
      return (<div>
          <label key="member-label" className="control-label"><Message msgId="usergroups.groupMembers" /></label>
          <div key="member-list" style={
          {
              maxHeight: "200px",
              padding: "5px",
              overflow: "auto",
              boxShadow: "inset 0 2px 5px 0 #AAA"
          }} >{this.renderMembers()}</div>
          <div key="add-member" >
              <label key="add-member-label" className="control-label"><Message msgId="usergroups.addMember" /></label>
              <Select
                  isLoading={this.props.availableUsersLoading}
                  options={availableUsers}
                  onOpen={this.props.searchUsers}
                  onInputChange={this.props.searchUsers}
                  onChange={(selected) => {
                      let value = selected.value;
                      let newMemberIndex = findIndex(this.props.availableUsers, u => u.id === value);
                      if (newMemberIndex >= 0) {
                          let newMember = this.props.availableUsers[newMemberIndex];
                          let newUsers = this.getCurrentGroupMembers();
                          newUsers = [...newUsers, newMember];
                          this.props.onChange("newUsers", newUsers);
                      }
                  }}
              />
          </div>
      </div>);
  },
  render() {
      return (<Dialog
            onClickOut={this.props.onClose}
            modal={true}
            maskLoading={this.props.group && (this.props.group.status === "loading" || this.props.group.status === "saving")}
            id="mapstore-group-dialog"
            className="group-edit-dialog"
            style={assign({}, this.props.style, {display: this.props.show ? "block" : "none"})}
            >
          <span role="header">
              <button onClick={this.props.onClose} className="login-panel-close close">
                  {this.props.closeGlyph ? <Glyphicon glyph={this.props.closeGlyph}/> : <span>×</span>}
              </button>
              <span className="user-panel-title">{(this.props.group && this.props.group.groupName) || <Message msgId="usergroups.newGroup" />}</span>
          </span>
          <div role="body">
          <Tabs defaultActiveKey={1} key="tab-panel">
              <Tab eventKey={1} title={<Button className="square-button" bsSize={this.props.buttonSize} bsStyle="primary"><Glyphicon glyph="1-group"/></Button>} >
                  {this.renderGeneral()}
                  {this.checkNameLenght()}
                  {this.checkDescLenght()}
              </Tab>
              <Tab eventKey={2} title={<Button className="square-button" bsSize={this.props.buttonSize} bsStyle="primary"><Glyphicon glyph="1-group-add"/></Button>} >
                  {this.renderMembersTab()}
              </Tab>
          </Tabs>
          </div>
          <div role="footer">
              {this.renderError()}
              {this.renderButtons()}
          </div>
      </Dialog>);
  },
  checkNameLenght() {
      return this.props.group && this.props.group.groupName && this.props.group.groupName.length === this.props.nameLimit ? (<div className="alert alert-warning">
            <Message msgId="usergroups.nameLimit"/>
        </div>) : null;
  },
  checkDescLenght() {
      return this.props.group && this.props.group.description && this.props.group.description.length === this.props.descLimit ? (<div className="alert alert-warning">
            <Message msgId="usergroups.descLimit"/>
        </div>) : null;
  },
  isSaving() {
      return this.props.group && this.props.group.status === "saving";
  },
  isSaved() {
      return this.props.group && (this.props.group.status === "saved" || this.props.group.status === "created");
  },
  isValid() {
      let valid = true;
      let group = this.props.group;
      if (!group) return false;
      valid = valid && group.groupName && group.status === "modified";
      return valid;
  },
  handleChange(event) {
      this.props.onChange(event.target.name, event.target.value);
  }

});

module.exports = GroupDialog;
