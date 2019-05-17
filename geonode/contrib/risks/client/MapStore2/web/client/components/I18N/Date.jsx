/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var {FormattedDate} = require('react-intl');

var DateFormat = React.createClass({
    propTypes: {
        value: React.PropTypes.object,
        dateParams: React.PropTypes.object
    },
    contextTypes: {
      intl: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            value: new Date()
        };
    },
    render() {
        return this.context.intl ? <FormattedDate value={this.props.value} {...this.props.dateParams}/> : <span>{this.props.value && this.props.value.toString() || ''}</span>;
    }
});

module.exports = DateFormat;
