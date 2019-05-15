/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {connect} = require('react-redux');
const {bindActionCreators} = require('redux');

const assign = require('object-assign');

const {changeMapView} = require('../../../actions/map');

const mapType = "openlayers";
const WMap = require('../../../components/map/' + mapType + '/Map');
const Layer = require('../../../components/map/' + mapType + '/Layer');
const Feature = require('../../../components/map/' + mapType + '/Feature');
require('../../../components/map/' + mapType + '/plugins/index');

const FeatureGridMap = (props) => {
    let features = (props.selFeatures && props.selFeatures.length > 0) ? props.selFeatures : props.features;
    return props.map ?
        (
            <WMap {...props.map} {...props.actions}>
                {props.layers.map((layer, index) =>
                    <Layer key={layer.name} position={index} type={layer.type}
                        options={assign({}, layer, {srs: props.map.projection})}/>
                )}
                <Layer type="vector" position={1} options={{name: "States"}}>
                {
                    features.map( (feature) => {
                        return (<Feature
                            key={feature.id}
                            type={feature.type}
                            geometry={feature.geometry}/>);
                    })
                }
                </Layer>
            </WMap>
        ) : <span/>;
};

FeatureGridMap.propTypes = {
    mapType: React.PropTypes.string,
    features: React.PropTypes.array,
    selFeatures: React.PropTypes.array
};

FeatureGridMap.defaultProps = {
    mapType: 'openlayers',
    features: [],
    selFeatures: []
};

module.exports = connect((state) => {
    return {
        map: state.map || (state.config && state.config.map),
        layers: state.config && state.config.layers || [],
        features: state.featuregrid.jsonlayer.features || [],
        selFeatures: state.featuregrid.select || null
    };
}, dispatch => {
    return {
        actions: bindActionCreators({
            onMapViewChanges: changeMapView
        }, dispatch)
    };
})(FeatureGridMap);
