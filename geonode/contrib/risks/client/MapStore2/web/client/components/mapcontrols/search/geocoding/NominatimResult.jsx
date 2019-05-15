/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');


let NominatimResult = React.createClass({
    propTypes: {
        item: React.PropTypes.object,
        onItemClick: React.PropTypes.func
    },
    onClick() {
        let item = this.props.item;
        this.props.onItemClick(item);
    },
    render() {
        if (this.props.item === undefined) {
            return null;
        }
        let item = this.props.item;
        return (
            <div key={item.osm_id} className="search-result NominatimResult" onClick={this.onClick}>
                <div className="icon"> <img src={item.icon} /></div>
                {item.display_name}
            </div>
        );
    }
});

module.exports = NominatimResult;
