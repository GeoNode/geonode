/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

 /* DESCRIPTION
    This component it creates a qr code base on the url passed via the shareUrl property
 */

import React from 'react';
const QRCode = require('qrcode.react');
const Message = require('../../components/I18N/Message');

const ShareQRCode = React.createClass({
    propTypes: {
        shareUrl: React.PropTypes.string
    },
  render() {
      return (
        <div className="qr-code">
            <h4>
                 <Message msgId="share.QRCodeLinkTitle"/>
            </h4>
          <QRCode value={this.props.shareUrl} />
      </div>
    );
  }
});

module.exports = ShareQRCode;
