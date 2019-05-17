/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const SharingLink = require('./SharingLink');
const Message = require('../I18N/Message');
const {OverlayTrigger, Popover, Button, Glyphicon} = require('react-bootstrap');

const SharingLinks = React.createClass({
    propTypes: {
        links: React.PropTypes.array,
        onCopy: React.PropTypes.func,
        messages: React.PropTypes.object,
        locale: React.PropTypes.string,
        buttonSize: React.PropTypes.string,
        popoverContainer: React.PropTypes.object,
        addAuthentication: React.PropTypes.bool
    },
    render() {
        if (!this.props.links || this.props.links.length === 0) {
            return null;
        }
        const {links, buttonSize, ...other} = this.props;
        const sharingLinks = links.map((link, index) => (<SharingLink key={index} url={link.url} labelId={link.labelId} {...other}/>));
        const popover = (<Popover className="links-popover" id="links-popover">{sharingLinks}</Popover>);
        return (
            <OverlayTrigger container={this.props.popoverContainer} positionLeft={150} placement="top" trigger="click" overlay={popover}>
                <Button bsSize={buttonSize} bsStyle="primary">
                    <Glyphicon glyph="link"/>&nbsp;<Message msgId="catalog.share"/>
                </Button>
            </OverlayTrigger>
        );
    }
});

module.exports = SharingLinks;
