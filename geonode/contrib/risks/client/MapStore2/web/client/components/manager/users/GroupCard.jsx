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

const GroupCard = React.createClass({
    propTypes: {
        // props
        style: React.PropTypes.object,
        group: React.PropTypes.object,
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
            innerItemStyle: {"float": "left", margin: "10px"}
        };
    },
    renderStatus() {
        return (<div key="status" className="user-status" style={{position: "absolute", bottom: 0, left: "10px", margin: "10px 10px 0 10px"}}>
           <div><strong><Message msgId="users.statusTitle"/></strong></div>
           {this.props.group.enabled ?
               <Glyphicon glyph="ok-sign"/> :
               <Glyphicon glyph="minus-sign"/>}
       </div>);
    },
    renderAvatar() {
        return (<div key="avatar" style={this.props.innerItemStyle} ><Button bsStyle="primary" type="button" className="square-button">
            <Glyphicon glyph="1-group" />
            </Button></div>);
    },
    renderDescription() {
        return (<div className="group-thumb-description">
            <div><strong><Message msgId="usergroups.description" /></strong></div>
            <div>{this.props.group.description ? this.props.group.description : <Message msgId="usergroups.noDescriptionAvailable" />}</div>
        </div>);
    },
    render() {
        return (
           <GridCard className="group-thumb" style={this.props.style} header={this.props.group.groupName}
                actions={this.props.actions}
               >
            {this.renderAvatar()}
            {this.renderStatus()}
            {this.renderDescription()}
           </GridCard>
        );
    }
});

module.exports = GroupCard;
