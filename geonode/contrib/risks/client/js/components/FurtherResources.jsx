/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');

const FurtherResources = React.createClass({
    propTypes: {
        analysisType: React.PropTypes.array,
        hazardType: React.PropTypes.array
    },
    getDefaultProps() {
        return {
        };
    },
    getResources(resources = []) {
        return resources.map((res, idx) => (
            <a target="_blank" href={res.details} key={idx}>
              <div className="row" style={{width: '100%'}}>
                <div className="col-xs-2"><i className="fa fa-dot-circle-o" /></div>
                <div className="col-xs-10">{res.text}</div>
            </div>
                </a>)
        );
    },
    render() {
        const {analysisType, hazardType} = this.props;
        const resources = [...analysisType, ...hazardType];
        return resources.length > 0 ? (
            <div id="disaster-further-resources" className="disaster-fth-res-container">
                <h4>Further Resources</h4>
                <p>For further information the following resources could be consulted:</p>
                <div className="container-fluid">
                    {this.getResources(resources)}
                </div>
            </div>) : <div id="disaster-further-resources"></div>;
    }
});

module.exports = FurtherResources;
