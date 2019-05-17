/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var BootstrapReact = require('react-bootstrap');
var I18N = require('../I18N/I18N');
var ListGroupItem = BootstrapReact.ListGroupItem;
var Button = BootstrapReact.Button;
var Glyphicon = BootstrapReact.Glyphicon;
var Tooltip = BootstrapReact.Tooltip;
var OverlayTrigger = BootstrapReact.OverlayTrigger;
var {isFunction} = require('lodash');

var MapItem = React.createClass({
    propTypes: {
        map: React.PropTypes.object,
        viewerUrl: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.func]),
        mapType: React.PropTypes.string
    },
    renderButtons: function() {
        if (this.props.viewerUrl) {
            let button = isFunction(this.props.viewerUrl) ?
            <Button bsStyle="info" onClick={() => this.props.viewerUrl(this.props.map)}> <Glyphicon glyph={"new-window"}/></Button> :
            <Button bsStyle="info" target="_blank" href={this.props.viewerUrl + "?type=" + this.props.mapType + "&mapId=" + this.props.map.id}> <Glyphicon glyph={"new-window"}/></Button>;
            const tooltip = <Tooltip id="manager.openInANewTab"><I18N.Message msgId="manager.openInANewTab" /></Tooltip>;
            return (<span style={{display: "block"}}>
                <OverlayTrigger placement="right" overlay={tooltip}>
                    {button}
                </OverlayTrigger>
            </span>);
        }
        return "";
    },
    render: function() {
        return (
           <ListGroupItem header={this.props.map.name}>{this.props.map.description} {this.renderButtons()}</ListGroupItem>
        );
    }
});

module.exports = MapItem;
