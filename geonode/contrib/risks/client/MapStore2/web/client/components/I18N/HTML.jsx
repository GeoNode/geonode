/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactIntl = require('react-intl');
var FormattedHTMLMessage = ReactIntl.FormattedHTMLMessage;

var Message = React.createClass({
    propTypes: {
        msgId: React.PropTypes.string.isRequired,
        msgParams: React.PropTypes.object
    },
    contextTypes: {
      intl: React.PropTypes.object
    },
    render() {
        return this.context.intl ? <FormattedHTMLMessage id={this.props.msgId} values={this.props.msgParams}/> : <span>{this.props.msgId || ""}</span>;
    }
});
module.exports = Message;
