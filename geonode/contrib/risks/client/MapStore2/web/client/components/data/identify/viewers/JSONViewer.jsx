/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var PropertiesViewer = require('./row/PropertiesViewer');

var JSONViewer = React.createClass({
    propTypes: {
        response: React.PropTypes.object,
        rowViewer: React.PropTypes.object
    },
    shouldComponentUpdate(nextProps) {
        return nextProps.response !== this.props.response;
    },
    render() {
        const RowViewer = this.props.rowViewer || PropertiesViewer;
        return (<div style={{maxHeight: "250px"}}>
                {(this.props.response.features || []).map((feature, i) => {
                    return <RowViewer key={i} title={feature.id} exclude={["bbox"]} {...feature.properties}/>;
                })}
            </div>
        );
    }
});

module.exports = JSONViewer;
