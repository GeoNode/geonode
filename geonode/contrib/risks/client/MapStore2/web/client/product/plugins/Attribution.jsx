/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const src = require("./attribution/geosolutions-brand.png");
const assign = require('object-assign');

const Attribution = React.createClass({
    propTypes: {
        src: React.PropTypes.string,
        style: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            src: src,
            style: {
                position: "absolute",
                width: "124px",
                left: 0,
                bottom: 0
            }
        };
    },

    render() {

        return (<img
                src={this.props.src}
                style={this.props.style} />);
    }
});

module.exports = {
    AttributionPlugin: assign(Attribution, {
        OmniBar: {
            position: 1,
            tool: () => <div className="navbar-header"><img className="customer-logo" src={src} height="36" /></div>,
            priority: 1
        }
    })
};
