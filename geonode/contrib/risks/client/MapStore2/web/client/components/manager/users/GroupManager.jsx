/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
// const Message = require('../I18N/Message');
const {ListGroup, ListGroupItem, Button, Glyphicon} = require('react-bootstrap');

const GroupManager = React.createClass({
    propTypes: {
        // props
        groups: React.PropTypes.object,
        style: React.PropTypes.object,
        onDeleteGroup: React.PropTypes.func,
        onCreateGroup: React.PropTypes.func,
        user: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            groups: [],
            onUserGroupsChange: () => {},
            user: {}
        };
    },
    render: function() {
        return (
           <div key="groups-manager">
               <Button key="create-btn" bsStyle="success" bsSize="small"><Glyphicon glyph="sign-plus" />Create New Group</Button>
               <ListGroup style={this.props.style} key="groups-available" bsSize="small">
                   {this.props.groups.map( group => (<ListGroupItem>
                       {group.groupName}
                       <Button style={{
                               "float": "right",
                               padding: "1px 5px",
                               fontSize: "12px",
                               lineHeight: 1.5
                       }} bsStyle="danger">X</Button>
                       </ListGroupItem>))}
               </ListGroup>
         </div>
        );
    }
});
/*

*/

module.exports = GroupManager;
