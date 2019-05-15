/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
require("./basicSpinner.css");

let BasicSpinner = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        value: React.PropTypes.number,
        sSize: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            id: "mapstore-basicspinner",
            value: null,
            sSize: null
        };
    },
    render() {
        return (
                <div className="spinner">
                    <div className={ "spinner-card " + this.props.sSize}>
                        <div className="spinner-bg spinner-loader" >Loading..</div>
                        <div className="spinner-fg">{this.props.value}</div>
                    </div>
                </div>
            );
    }

});

module.exports = BasicSpinner;
