/**
* Copyright 2017, GeoSolutions Sas.
* All rights reserved.
*
* This source code is licensed under the BSD-style license found in the
* LICENSE file in the root directory of this source tree.
*/

const {createSelector} = require('reselect');
const {head, findIndex} = require('lodash');
const assign = require('object-assign');
const MapInfoUtils = require('../../MapStore2/web/client/utils/MapInfoUtils');
const LayersUtils = require('../../MapStore2/web/client/utils/LayersUtils');
const {getViewParam, getLayerName, getStyle} = require('../utils/DisasterUtils');
const layersSelectorO = state => (state.layers && state.layers.flat) || (state.layers) || (state.config && state.config.layers);
const markerSelector = state => (state.mapInfo && state.mapInfo.showMarker && state.mapInfo.clickPoint);
const geoColderSelector = state => (state.search && state.search.markerPosition);
const disasterSelector = state => ({
    riskAnalysis: state.disaster && state.disaster.riskAnalysis,
    dim: state.disaster && state.disaster.dim || {dim1: 0, dim2: 1, dim1Idx: 0, dim2Idx: 0},
    showSubUnit: state.disaster.showSubUnit,
    app: state.disaster && state.disaster.app
});
// TODO currently loading flag causes a re-creation of the selector on any pan
// to avoid this separate loading from the layer object
const layersSelector = createSelector([layersSelectorO, disasterSelector],
    (layers = [], disaster) => {
        let newLayers;
        const riskAnWMSIdx = findIndex(layers, l => l.id === '_riskAn_');
        if (disaster.riskAnalysis && riskAnWMSIdx !== -1) {
            const riskAnWMS = assign({}, layers[riskAnWMSIdx], {name: getLayerName(disaster), style: getStyle(disaster), params: getViewParam(disaster)});
            newLayers = layers.slice();
            newLayers.splice(riskAnWMSIdx, riskAnWMSIdx, riskAnWMS);
        }else {
            newLayers = [...layers];
        }
        return newLayers;
    });

const layerSelectorWithMarkers = createSelector(
    [layersSelector, markerSelector, geoColderSelector, disasterSelector],
    (layers = [], markerPosition, geocoderPosition) => {
        let newLayers = [...layers];
        if ( markerPosition ) {
            newLayers.push(MapInfoUtils.getMarkerLayer("GetFeatureInfo", markerPosition.latlng));
        }
        if (geocoderPosition) {
            newLayers.push(MapInfoUtils.getMarkerLayer("GeoCoder", geocoderPosition, "marker",
                {
                    overrideOLStyle: true,
                    style: {
                        iconUrl: "https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
                        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                        iconSize: [25, 41],
                        iconAnchor: [12, 41],
                        popupAnchor: [1, -34],
                        shadowSize: [41, 41]
                    }
                }
            ));
        }

        return newLayers;
    }
);
const disasterRiskLayerSelector = createSelector([layerSelectorWithMarkers],
    (layers) => ({
        layer: head(layers.filter((l) => l.id === "_riskAn_"))
    }));
const groupsSelector = (state) => state.layers && state.layers.flat && state.layers.groups && LayersUtils.denormalizeGroups(state.layers.flat, state.layers.groups).groups || [];

module.exports = {
    layersSelector,
    layerSelectorWithMarkers,
    groupsSelector,
    disasterRiskLayerSelector
};
