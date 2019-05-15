/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');


let Feature = React.createClass({
    propTypes: {
        type: React.PropTypes.string,
        container: React.PropTypes.object, // TODO it must be a L.GeoJSON
        geometry: React.PropTypes.object
    },
    componentDidMount() {
    },
    componentWillUnmount() {
    },
    render() {
        return null;
    }
});

module.exports = Feature;
