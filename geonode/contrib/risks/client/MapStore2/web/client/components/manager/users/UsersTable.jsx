/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Button, Glyphicon, Table, OverlayTrigger, Tooltip} = require('react-bootstrap');
const Message = require('../../I18N/Message');
var UsersTable = React.createClass({
    propTypes: {
        users: React.PropTypes.array,
        deleteToolTip: React.PropTypes.string,
        onRemove: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            users: [],
            deleteToolTip: "usergroups.removeUser",
            onRemove: () => {}
        };
    },
    render: function() {
        return (<Table striped condensed hover><tbody>{this.props.users.map((user) => {
            let tooltip = <Tooltip id="tooltip"><Message msgId={this.props.deleteToolTip} /></Tooltip>;
            return (<tr>
                      <td><Glyphicon glyph="user" /> {user.name}</td>
                      <td>
                          <OverlayTrigger placement="left" overlay={tooltip}>
                              <Button style={{"float": "right"}} bsSize="xs" onClick={() => {
                                  this.props.onRemove(user);
                              }}>
                                  <Glyphicon glyph="remove-circle"/>
                              </Button>
                          </OverlayTrigger>
                          </td>
                      </tr>
                      );
        })}</tbody></Table>);
    }
});

module.exports = UsersTable;
