/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

/*  DESCRIPTION
    This component contains the code and the button for copy the embedded code
    to the clipboard
*/

// components required
const React = require('react');
const CopyToClipboard = require('react-copy-to-clipboard');
const Message = require('../../components/I18N/Message');
const {Glyphicon, Col, Grid, Row, Tooltip, OverlayTrigger, Button} = require('react-bootstrap');


// css required
require('./share.css');

const ShareEmbed = React.createClass({
    propTypes: {
        shareUrl: React.PropTypes.string
    },
    getInitialState() {
        return {copied: false};
    },
  render() {

      const codeEmbedded = "<iframe style=\"border: none;\" height=\"400\" width=\"600\" src=\"" + this.props.shareUrl + "\"></iframe>";
      const tooltip = (<Tooltip placement="bottom" className="in" id="tooltip-bottom" style={{zIndex: 2001}}>
                           {this.state.copied ? <Message msgId="share.msgCopiedUrl"/> : <Message msgId="share.msgToCopyUrl"/>}
                       </Tooltip>);
      const copyTo = (<OverlayTrigger placement="bottom" overlay={tooltip}>
                          <CopyToClipboard text={codeEmbedded} onCopy={ () => this.setState({copied: true}) } >
                              <Button className="buttonCopyTextArea" bsStyle="info" bsSize="large">
                                  <Glyphicon glyph="copy" onMouseLeave={() => {this.setState({copied: false}); }} />
                              </Button>
                          </CopyToClipboard>
                      </OverlayTrigger>);
      return (
          <div className="input-link">
              <Grid className="embed-box" fluid={true}>
                  <Row key="title">
                        <h4>
                           <Message msgId="share.embeddedLinkTitle"/>
                        </h4>
                    </Row>
                    <Row key="data" className="row-button">
                        <Col key="textarea" xs={10} sm={10} md={10}><textarea name="description" rows="6" value={codeEmbedded} enabled="false" readOnly /></Col>
                        <Col key="button" xs={2} sm={2} md={2}>
                            {copyTo}
                        </Col>
                    </Row>
                </Grid>
          </div>
      );
  }
});

module.exports = ShareEmbed;
