/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactIntl = require('react-intl');

const FormattedMessage = ReactIntl.FormattedMessage;

const Message = React.createClass({
    propTypes: {
        msgId: React.PropTypes.string.isRequired,
        msgParams: React.PropTypes.object
    },
    contextTypes: {
        intl: React.PropTypes.object
    },
    render() {
        return this.context.intl ? <FormattedMessage id={this.props.msgId} values={this.props.msgParams}/> : <span>{this.props.msgId || ""}</span>;
    }
});

module.exports = Message;
