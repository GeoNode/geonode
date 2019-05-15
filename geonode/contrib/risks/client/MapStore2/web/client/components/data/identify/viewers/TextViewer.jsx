/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');

const TextViewer = React.createClass({
    propTypes: {
        response: React.PropTypes.string
    },
    shouldComponentUpdate(nextProps) {
        return nextProps.response !== this.props.response;
    },
    render() {
        return (<pre>{this.props.response}</pre>);
    }
});

module.exports = TextViewer;
