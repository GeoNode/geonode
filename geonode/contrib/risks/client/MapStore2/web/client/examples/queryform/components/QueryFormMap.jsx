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
const url = require('url');
const urlQuery = url.parse(window.location.href, true).query;
const {
    changeDrawingStatus,
    endDrawing
} = require('../../../actions/draw');

const mapType = urlQuery.map ? urlQuery.map : "leaflet";
const WMap = require('../../../components/map/' + mapType + '/Map');
const Layer = require('../../../components/map/' + mapType + '/Layer');
require('../../../components/map/' + mapType + '/plugins/index');

const DrawSupport = require('../../../components/map/' + mapType + '/DrawSupport');

const QueryFormMap = (props) => {
    return props.map ?
        (
            <WMap {...props.map} {...props.actions}>
                {props.layers.map((layer, index) =>
                    <Layer key={layer.name} position={index} type={layer.type}
                        options={assign({}, layer, {srs: props.map.projection})}/>
                )}
                <DrawSupport
                    map={props.map}
                    drawStatus={props.drawStatus}
                    drawOwner={props.drawOwner}
                    drawMethod={props.drawMethod}
                    features={props.features}
                    onChangeDrawingStatus={props.actions.onChangeDrawingStatus}
                    onEndDrawing={props.actions.onEndDrawing}/>
            </WMap>
        ) : <span/>;
};

QueryFormMap.propTypes = {
    mapType: React.PropTypes.string,
    drawStatus: React.PropTypes.string,
    drawOwner: React.PropTypes.string,
    drawMethod: React.PropTypes.string,
    features: React.PropTypes.array
};

QueryFormMap.defaultProps = {
    mapType: 'leaflet',
    drawStatus: null,
    drawOwner: null,
    drawMethod: null,
    features: []
};

module.exports = connect((state) => {
    return {
        map: (state.map && state.map) || (state.config && state.config.map),
        layers: state.config && state.config.layers || [],
        drawStatus: state.draw.drawStatus,
        drawOwner: state.draw.drawOwner,
        drawMethod: state.draw.drawMethod,
        features: state.draw.features
    };
}, dispatch => {
    return {
        actions: bindActionCreators({
            onMapViewChanges: changeMapView,
            onChangeDrawingStatus: changeDrawingStatus,
            onEndDrawing: endDrawing
        }, dispatch)
    };
})(QueryFormMap);
