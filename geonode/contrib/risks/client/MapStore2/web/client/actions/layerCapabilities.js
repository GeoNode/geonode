/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {updateNode} = require('./layers');
const WMS = require('../api/WMS');
const WFS = require('../api/WFS');
const WCS = require('../api/WCS');

const _ = require('lodash');

function getDescribeLayer(url, layer, options) {
    return (dispatch /* , getState */) => {
        return WMS.describeLayer(url, layer.name, options).then((describeLayer) => {
            if (describeLayer && describeLayer.owsType === "WFS") {
                return WFS.describeFeatureType(url, describeLayer.name).then((describeFeatureType) => {
                    // TODO move the management of this geometryType in the proper components, getting the describeFeatureType entry:
                    let types = _.get(describeFeatureType, "complexType[0].complexContent.extension.sequence.element");
                    let geometryType = _.head(types && types.filter( elem => (elem.name === "the_geom" || elem.type.prefix.indexOf("gml") === 0)));
                    geometryType = geometryType && geometryType.type.localPart;
                    describeLayer.geometryType = geometryType && geometryType.split("PropertyType")[0];
                    return dispatch(updateNode(layer.id, "id", {describeLayer, describeFeatureType}));
                }).catch(() => {
                    return dispatch(updateNode(layer.id, "id", {describeLayer: describeLayer || {"error": "no describe feature found"}}));
                });
            } else if ( describeLayer && describeLayer.owsType === "WCS" ) {
                WCS.describeCoverage(url, describeLayer.name).then((describeCoverage) => {
                    // TODO move the management of this bands in the proper components, getting the describeFeatureType entry:
                    let axis = _.get(describeCoverage, "wcs:CoverageDescriptions.wcs:CoverageDescription.wcs:Range.wcs:Field.wcs:Axis.wcs:AvailableKeys.wcs:Key");
                    if (axis && typeof axis === "string") {
                        describeLayer.bands = [1 + ""];
                    } else {
                        describeLayer.bands = axis.map((el, index) => ((index + 1) + "")); // array of 1 2 3 because the sld do not recognize the name
                    }

                    dispatch(updateNode(layer.id, "id", {describeLayer, describeCoverage}));
                }).catch(() => {
                    return dispatch(updateNode(layer.id, "id", {describeLayer: describeLayer || {"error": "no describe coverage found"}}));
                });
            }
            return dispatch(updateNode(layer.id, "id", {describeLayer: describeLayer || {"error": "no describe Layer found"}}));

        });
    };
}

function getLayerCapabilities(layer, options) {
    // geoserver's specific. TODO parse layer.capabilitiesURL.
    let reqUrl = layer.url;
    let urlParts = reqUrl.split("/geoserver/");
    if (urlParts.length === 2) {
        let layerParts = layer.name.split(":");
        if (layerParts.length === 2) {
            reqUrl = urlParts[0] + "/geoserver/" + layerParts [0] + "/" + layerParts[1] + "/" + urlParts[1];
        }
    }
    return (dispatch) => {
        // TODO, look ad current cached capabilities;
        dispatch(updateNode(layer.id, "id", {
            capabilitiesLoading: true
        }));
        return WMS.getCapabilities(reqUrl, options).then((capabilities) => {
            let layers = _.get(capabilities, "capability.layer.layer");
            let layerCapability;

            layerCapability = _.head(layers.filter( ( capability ) => {
                if (layer.name.split(":").length === 2 && capability.name && capability.name.split(":").length === 2 ) {
                    return layer.name === capability.name;
                } else if (capability.name && capability.name.split(":").length === 2) {
                    return (layer.name === capability.name.split(":")[1]);
                } else if (layer.name.split(":").length === 2) {
                    return layer.name.split(":")[1] === capability.name;
                }
                return layer.name === capability.name;
            }));
            if (layerCapability) {
                dispatch(updateNode(layer.id, "id", {
                    capabilities: layerCapability,
                    capabilitiesLoading: null,
                    boundingBox: layerCapability.latLonBoundingBox,
                    availableStyles: layerCapability.style && (Array.isArray(layerCapability.style) ? layerCapability.style : [layerCapability.style])
                }));
            }
            // return dispatch(updateNode(layer.id, "id", {capabilities: capabilities || {"error": "no describe Layer found"}}));

        }).catch((error) => {
            dispatch(updateNode(layer.id, "id", {capabilitiesLoading: null, capabilities: {error: "error getting capabilities", details: error}} ));

            // return dispatch(updateNode(layer.id, "id", {capabilities: capabilities || {"error": "no describe Layer found"}}));

        });
    };
}

module.exports = {
    getDescribeLayer, getLayerCapabilities
};
