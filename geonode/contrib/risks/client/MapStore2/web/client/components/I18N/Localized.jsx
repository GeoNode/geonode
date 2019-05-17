/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {IntlProvider} = require('react-intl');

const Localized = React.createClass({
    propTypes: {
        locale: React.PropTypes.string,
        messages: React.PropTypes.object,
        loadingError: React.PropTypes.string
    },
    childContextTypes: {
        locale: React.PropTypes.string,
        messages: React.PropTypes.object
    },
    getChildContext() {
        return {
           locale: this.props.locale,
           messages: this.props.messages
        };
    },
    render() {
        let { children } = this.props;

        if (this.props.messages && this.props.locale) {
            if (typeof children === 'function') {
                children = children();
            }

            return (<IntlProvider key={this.props.locale} locale={this.props.locale}
                 messages={this.flattenMessages(this.props.messages)}
                >
                {children}
            </IntlProvider>);
            // return React.Children.only(children);
        } else if (this.props.loadingError) {
            return <div className="loading-locale-error">{this.props.loadingError}</div>;
        }
        return null;
    },
    flattenMessages(messages, prefix = '') {
        return Object.keys(messages).reduce((previous, current) => {
            return (typeof messages[current] === 'string') ? {
                 [prefix + current]: messages[current],
                ...previous
            } : {
                ...this.flattenMessages(messages[current], prefix + current + '.'),
                ...previous
            };
        }, {});
    }
 });

module.exports = Localized;
