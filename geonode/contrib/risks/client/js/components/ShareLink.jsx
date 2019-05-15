/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

/*  DESCRIPTION
    This component contain an input field for holding the url and an icon to
    copy to the clipbard the relatie url.
*/

// components required
const React = require('react');
const CopyToClipboard = require('react-copy-to-clipboard');
const {Tooltip, OverlayTrigger, Button} = require('react-bootstrap');

const ShareLink = React.createClass({
    propTypes: {
        shareUrl: React.PropTypes.string
    },
    getInitialState() {
        return {copied: false};
    },
    render() {
        const tooltip = (
            <Tooltip className="disaster" placement="bottom" id="tooltip-share" style={{zIndex: 2001}}>
                {this.state.copied ? 'The link has been copied' : 'Click to get the permalink of this page'}
            </Tooltip>
        );
        return (
            <OverlayTrigger placement="bottom" overlay={tooltip}>
                <CopyToClipboard text={this.props.shareUrl} onCopy={ () => this.setState({copied: true}) } >
                    <Button id="disaster-share-link" style={this.state.copied ? {backgroundColor: '#ff8f31'} : {}} bsStyle="primary" onMouseLeave={() => {this.setState({copied: false}); }} >
                        <i className="fa fa-share" />
                    </Button>
                </CopyToClipboard>
            </OverlayTrigger>
        );
    }
});

module.exports = ShareLink;
