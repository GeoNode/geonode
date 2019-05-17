/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {connect} = require('react-redux');
const {deleteGroup} = require('../../../actions/usergroups');
const {Alert} = require('react-bootstrap');
const Confirm = require('../../../components/misc/ConfirmDialog');
const GroupCard = require('../../../components/manager/users/GroupCard');
const Message = require('../../../components/I18N/Message');
const {findIndex} = require('lodash');

const GroupDeleteConfirm = React.createClass({
    propTypes: {
        group: React.PropTypes.object,
        deleteGroup: React.PropTypes.func,
        deleteId: React.PropTypes.number,
        deleteError: React.PropTypes.object,
        deleteStatus: React.PropTypes.string

    },
    getDefaultProps() {
        return {
            deleteGroup: () => {}
        };
    },
    renderError() {
        if (this.props.deleteError) {
            return <Alert bsStyle="danger"><Message msgId="usergroups.errorDelete" />{this.props.deleteError.statusText}</Alert>;
        }
    },
    renderConfirmButtonContent() {
        switch (this.props.deleteStatus) {
            case "deleting":
                return <Message msgId="users.deleting" />;
            default:
                return <Message msgId="users.delete" />;
        }
    },
    render() {
        if (!this.props.group) {
            return null;
        }
        return (<Confirm
            show={!!this.props.group}
            onClose={() => this.props.deleteGroup(this.props.deleteId, "cancelled")}
            onConfirm={ () => { this.props.deleteGroup(this.props.deleteId, "delete"); } }
            confirmButtonContent={this.renderConfirmButtonContent()}
            confirmButtonDisabled={this.props.deleteStatus === "deleting"}>
            <div><Message msgId="usergroups.confirmDeleteGroup" /></div>
            <div style={{margin: "10px 0"}}><GroupCard group={this.props.group} /></div>
            <div>{this.renderError()}</div>
        </Confirm>);
    }
});
module.exports = connect((state) => {
    let groupsstate = state && state.usergroups;
    if (!groupsstate) return {};
    let groups = groupsstate && groupsstate.groups;
    let deleteId = groupsstate.deletingGroup && groupsstate.deletingGroup.id;
    if (groups && deleteId) {
        let index = findIndex(groups, (user) => user.id === deleteId);
        let group = groups[index];
        return {
            group,
            deleteId,
            deleteError: groupsstate.deletingGroup.error,
            deleteStatus: groupsstate.deletingGroup.status
        };
    }
    return {
        deleteId
    };
}, {deleteGroup} )(GroupDeleteConfirm);
