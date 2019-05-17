/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
// const Message = require('../I18N/Message');
const Select = require('react-select');
const Message = require('../../I18N/Message');
const {findIndex} = require('lodash');

require('react-select/dist/react-select.css');

// const ConfirmModal = require('./modals/ConfirmModal');
// const GroupManager = require('./GroupManager');

const UserCard = React.createClass({
    propTypes: {
        // props
        groups: React.PropTypes.array,
        onUserGroupsChange: React.PropTypes.func,
        user: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            groups: [],
            onUserGroupsChange: () => {},
            user: {}
        };
    },

    onChange(values) {
        if (values === null) {
            return;
        }
        this.props.onUserGroupsChange("groups", values.map((group) => {
            let index = findIndex(this.props.groups, (availableGroup)=>availableGroup.id === group.value);
            return index >= 0 ? this.props.groups[index] : null;
        }).filter(group => group));
    },
    getDefaultGroups() {
        return this.props.groups.filter((group) => group.groupName === "everyone");
    },
    getOptions() {
        return this.props.groups.map((group) => ({
            label: group.groupName,
            value: group.id,
            clearableValue: group.groupName !== "everyone"
        }));
    },
    renderGroupsSelector() {
        return (<Select key="groupSelector"
        clearable={false}
        isLoading={this.props.groups.length === 0 }
        name="user-groups-selector"
        multi={true}
        value={ (this.props.user && this.props.user.groups ? this.props.user.groups : this.getDefaultGroups() ).map(group => group.id) }
        options={this.getOptions()}
        onChange={this.onChange}
        />);
    },
    render: function() {
        return (
           <div key="groups-page">
             <span><Message msgId="users.selectedGroups" /></span>
             {this.renderGroupsSelector()}
         </div>
        );
    }
});
/*

*/

module.exports = UserCard;
