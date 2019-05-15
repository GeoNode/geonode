/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const Message = require('../I18N/Message');
const {FormControl, FormGroup, Button, Glyphicon, OverlayTrigger, Tooltip} = require('react-bootstrap');
const CopyToClipboard = require('react-copy-to-clipboard');
const SecurityUtils = require('../../utils/SecurityUtils');

const SharingLink = React.createClass({
    propTypes: {
        url: React.PropTypes.string.isRequired,
        labelId: React.PropTypes.string,
        onCopy: React.PropTypes.func,
        bsSize: React.PropTypes.string,
        addAuthentication: React.PropTypes.bool
    },
    getDefaultProps() {
        return {
            onCopy: () => {},
            bsSize: 'small',
            addAuthentication: false
        };
    },
    getInitialState() {
        return {showCopiedToolTip: false};
    },
    render() {
        if (!this.props.url) {
            return null;
        }
        // add authentication to the url if possible
        const url = this.props.addAuthentication ? SecurityUtils.addAuthenticationToUrl(this.props.url) : this.props.url;
        const messageId = this.state.showCopiedToolTip ? "catalog.copied" : "catalog.copyToClipboard";
        const tooltip = (
            <Tooltip id="tooltip">
                <Message msgId={messageId}/>
            </Tooltip>
        );
        const copyButton = (
            <CopyToClipboard text={url} onCopy={this.props.onCopy}>
                <OverlayTrigger placement="right" overlay={tooltip} onExited={() => this.setState({showCopiedToolTip: false})}>
                    <Button bsSize={this.props.bsSize} bsStyle="primary" className="link-button" onClick={() => this.setState({showCopiedToolTip: true})}>
                        <Glyphicon glyph="paperclip"/>&nbsp;{this.props.labelId
                                && <Message msgId={this.props.labelId}/>}
                    </Button>
                </OverlayTrigger>
            </CopyToClipboard>
        );
        return (
            <div className="link-sharing">
                <FormGroup bsSize={this.props.bsSize} >
                  <FormControl className="link-input"
                    type="text" value={url} onChange={() => {}}/>
                  {copyButton}
                </FormGroup>
            </div>
        );
    }
});

module.exports = SharingLink;
