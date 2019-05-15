/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const defaultIcon = require('./img/spinner.gif');
const {isFunction} = require('lodash');

var InlineSpinner = React.createClass({
    propTypes: {
        className: React.PropTypes.string,
        loading: React.PropTypes.oneOfType([React.PropTypes.bool, React.PropTypes.func]),
        icon: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            loading: false,
            icon: defaultIcon,
            className: "inline-spinner"
        };
    },
    getDisplayStyle() {
        let loading;
        if (isFunction(this.props.loading)) {
            loading = this.props.loading(this.props);
        } else {
            loading = this.props.loading;
        }
        return (loading ? 'inline-block' : 'none');
    },
    render() {
        return (
            <img className={this.props.className} src={this.props.icon} style={{
                display: this.getDisplayStyle(),
                margin: '4px',
                padding: 0,
                background: 'transparent',
                border: 0
            }} alt="..." />
        );
    }
});

module.exports = InlineSpinner;
