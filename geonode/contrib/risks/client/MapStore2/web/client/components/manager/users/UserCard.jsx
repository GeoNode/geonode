/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
// const Message = require('../I18N/Message');
const GridCard = require('../../misc/GridCard');
const {Button, Glyphicon} = require('react-bootstrap');
const Message = require('../../../components/I18N/Message');


// const ConfirmModal = require('./modals/ConfirmModal');

require('./style/usercard.css');

const UserCard = React.createClass({
    propTypes: {
        // props
        style: React.PropTypes.object,
        user: React.PropTypes.object,
        innerItemStyle: React.PropTypes.object,
        actions: React.PropTypes.array
    },
    getDefaultProps() {
        return {
            style: {
                position: "relative",
                backgroundSize: "cover",
                backgroundPosition: "center",
                backgroundRepeat: "repeat-x"
            },
            innerItemStyle: {"float": "left",
                margin: "10px"
            }
        };
    },
    renderStatus() {
        return (<div key="status" className="user-status" style={{position: "absolute", bottom: 0, left: "10px", margin: "10px 10px 0 10px"}}>
           <div><strong><Message msgId="users.statusTitle"/></strong></div>
           {this.props.user.enabled ?
               <Glyphicon glyph="ok-sign"/> :
               <Glyphicon glyph="minus-sign"/>}
       </div>);
    },
    renderGroups() {
        return (<div key="groups" className="groups-container" style={this.props.innerItemStyle}><div><strong><Message msgId="users.groupTitle"/></strong></div>
    <div className="groups-list">{this.props.user && this.props.user.groups ? this.props.user.groups.map((group) => (<div className="group-item" key={"group-" + group.id}>{group.groupName}</div>)) : null}</div>

     </div>);
    },
    renderRole() {
        return (<div key="role" className="role-containter" style={this.props.innerItemStyle}><div><strong><Message msgId="users.roleTitle"/></strong></div>
            {this.props.user.role}
        </div>);
    },
    renderAvatar() {
        return (<div key="avatar" className="avatar-containter" style={this.props.innerItemStyle} ><Button bsStyle="primary" type="button" className="square-button">
            <Glyphicon glyph="user" />
            </Button></div>);
    },
    render() {
        return (
           <GridCard className="user-thumb" style={this.props.style} header={this.props.user.name}
                actions={this.props.actions}
               >
            <div className="user-data-container">
                {this.renderAvatar()}
                {this.renderRole()}
                {this.renderGroups()}
            </div>
             {this.renderStatus()}
           </GridCard>
        );
    }
});

module.exports = UserCard;
