/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {connect} = require('react-redux');
const {Button, Grid, Glyphicon} = require('react-bootstrap');
const {editGroup} = require('../../actions/usergroups');
const {getUserGroups, groupSearchTextChanged} = require('../../actions/usergroups');
const SearchBar = require("../../components/mapcontrols/search/SearchBar");
const GroupsGrid = require('./users/GroupGrid');
const GroupDialog = require('./users/GroupDialog');
const GroupDeleteConfirm = require('./users/GroupDeleteConfirm');
const Message = require('../../components/I18N/Message');
const assign = require('object-assign');
const {trim} = require('lodash');
const GroupManager = React.createClass({
    propTypes: {
        onNewGroup: React.PropTypes.func,
        className: React.PropTypes.string,
        hideOnBlur: React.PropTypes.bool,
        placeholderMsgId: React.PropTypes.string,
        typeAhead: React.PropTypes.bool,
        searchText: React.PropTypes.string,
        onSearch: React.PropTypes.func,
        onSearchReset: React.PropTypes.func,
        onSearchTextChange: React.PropTypes.func,
        start: React.PropTypes.number,
        limit: React.PropTypes.number
    },
    getDefaultProps() {
        return {
            className: "user-search",
            hideOnBlur: false,
            placeholderMsgId: "usergroups.searchGroups",
            typeAhead: false,
            searchText: "",
            start: 0,
            limit: 20,
            onNewGroup: () => {},
            onSearch: () => {},
            onSearchReset: () => {},
            onSearchTextChange: () => {}
        };
    },
    onNew() {
        this.props.onNewGroup();
    },
    render() {
        return (<div>
            <SearchBar
                className={this.props.className}
                hideOnBlur={this.props.hideOnBlur}
                placeholderMsgId ={this.props.placeholderMsgId}
                onSearch={this.props.onSearch}
                onSearchReset={this.props.onSearchReset}
                onSearchTextChange={this.props.onSearchTextChange}
                typeAhead={this.props.typeAhead}
                searchText={this.props.searchText}
                start={this.props.start}
                limit={this.props.limit} />
            <Grid style={{marginBottom: "10px"}} fluid={true}>
                <h1 className="usermanager-title"><Message msgId={"usergroups.groups"}/></h1>
                <Button style={{marginRight: "10px"}} bsStyle="success" onClick={this.onNew}>
                    <span><Glyphicon glyph="1-group-add" />&nbsp;<Message msgId="usergroups.newGroup" /></span>
                </Button>
            </Grid>
            <GroupsGrid />
            <GroupDialog />
            <GroupDeleteConfirm />
        </div>);
    }
});
module.exports = {
    GroupManagerPlugin: assign(
        connect((state) => {
            let searchState = state && state.usergroups;
            return {
                start: searchState && searchState.start,
                limit: searchState && searchState.limit,
                searchText: (searchState && searchState.searchText && trim(searchState.searchText, '*')) || ""
            };
        }, {
            onNewGroup: editGroup.bind(null, {}),
            onSearchTextChange: groupSearchTextChanged,
            onSearch: getUserGroups
        }, (stateProps, dispatchProps) => {
            return {
                ...stateProps,
                ...dispatchProps,
                onSearchReset: (text) => {
                    let limit = stateProps.limit;
                    let searchText = (text && text !== "") ? ("*" + text + "*") : "*";
                    dispatchProps.onSearch(searchText, {params: {start: 0, limit}});
                },
                onSearch: (text) => {
                    let limit = stateProps.limit;
                    let searchText = (text && text !== "") ? ("*" + text + "*") : "*";
                    dispatchProps.onSearch(searchText, {params: {start: 0, limit}});
                }
            };
        })(GroupManager), {
    hide: true,
    Manager: {
        id: "groupmanager",
        name: 'groupmanager',
        position: 1,
        priority: 1,
        title: <Message msgId="usergroups.manageGroups" />,
        glyph: "1-group-mod"
    }}),
    reducers: {
        usergroups: require('../../reducers/usergroups')
    }
};
