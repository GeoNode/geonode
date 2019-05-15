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
const Message = require('../../components/I18N/Message');
const {Glyphicon, FormControl, FormGroup, Tooltip, OverlayTrigger, Button} = require('react-bootstrap');

// css required
require('./share.css');

const ShareLink = React.createClass({
    propTypes: {
        shareUrl: React.PropTypes.string
    },
    getInitialState() {
        return {copied: false};
    },
    render() {
        const tooltip = (<Tooltip placement="bottom" className="in" id="tooltip-bottom" style={{zIndex: 2001}}>
          {this.state.copied ? <Message msgId="share.msgCopiedUrl"/> : <Message msgId="share.msgToCopyUrl"/>}
      </Tooltip>);
        const copyTo = (<OverlayTrigger placement="bottom" overlay={tooltip}>
                            <CopyToClipboard text={this.props.shareUrl} onCopy={ () => this.setState({copied: true}) } >
                                <Button className="buttonCopy" bsStyle="info" bsSize="large" onMouseLeave={() => {this.setState({copied: false}); }} >
                                    <Glyphicon glyph="copy"/>
                                </Button>
                            </CopyToClipboard>
                        </OverlayTrigger>);
        return (
            <div className="input-link">
                  <h4>
                     <Message msgId="share.directLinkTitle"/>
                  </h4>
                  <FormGroup>
                      <div className="input-group">
                          <FormControl onFocus={ev => ev.target.select()} ref="copytext" type="text" value={this.props.shareUrl} readOnly/>
                          <span className="input-group-addon">{copyTo}</span>
                      </div>
                  </FormGroup>
            </div>
        );
    }
});

module.exports = ShareLink;
