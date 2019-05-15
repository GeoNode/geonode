/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {Button} = require('react-bootstrap');

const LinkToPage = React.createClass({
    propTypes: {
        params: React.PropTypes.object,
        url: React.PropTypes.string,
        txt: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        btProps: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            params: [],
            url: '',
            btProps: {},
            txt: 'Link'
        };
    },
    render() {
        return (
            <Button bsStyle="link" href={this.buildUrl()} target="_blank" {...this.props.btProps}>
            {this.props.txt}
            </Button>
        );
    },
    buildUrl() {
        let urlParams = '?';
        Object.keys(this.props.params).forEach(function(p) {
            urlParams += p + "=" + this.props.params[p] + "&";
        }, this);
        return this.props.url + encodeURI(urlParams);
    }
});

module.exports = LinkToPage;
