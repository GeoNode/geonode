/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const img = require('./images/magnifier.png');

const ZoomToFeatureRenderer = React.createClass({
    propTypes: {
        params: React.PropTypes.object
    },
    render() {
        const geometry = this.props.params && this.props.params.data && this.props.params.data.geometry;
        return geometry && geometry.coordinates ? (
            <img src={img} width={16}/>
        ) : null;
    }
});

module.exports = ZoomToFeatureRenderer;
