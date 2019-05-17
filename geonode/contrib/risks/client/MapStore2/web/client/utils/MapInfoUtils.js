/**
 * Copyright 2015-2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const FeatureInfoUtils = require("./FeatureInfoUtils");
const INFO_FORMATS = FeatureInfoUtils.INFO_FORMATS;
const INFO_FORMATS_BY_MIME_TYPE = FeatureInfoUtils.INFO_FORMATS_BY_MIME_TYPE;

const {isArray} = require('lodash');
const assign = require('object-assign');
const pointOnSurface = require('turf-point-on-surface');
const CoordinatesUtils = require('./CoordinatesUtils');
const MapUtils = require('./MapUtils');

const MapInfoUtils = {
    /**
     * specifies which info formats are currently supported
     */
    //           default format ↴
    AVAILABLE_FORMAT: ['TEXT', 'JSON', 'HTML'],

    /**
     * @return a filtered version of INFO_FORMATS object.
     * the returned object contains only keys that AVAILABLE_FORMAT contains.
     */
    getAvailableInfoFormat() {
        return Object.keys(INFO_FORMATS).filter((k) => {
            return MapInfoUtils.AVAILABLE_FORMAT.indexOf(k) !== -1;
        }).reduce((prev, k) => {
            prev[k] = INFO_FORMATS[k];
            return prev;
        }, {});
    },
    /**
     * @return like getAvailableInfoFormat but return an array filled with the keys
     */
    getAvailableInfoFormatLabels() {
        return Object.keys(MapInfoUtils.getAvailableInfoFormat());
    },
    /**
     * @return like getAvailableInfoFormat but return an array filled with the values
     */
    getAvailableInfoFormatValues() {
        return Object.keys(MapInfoUtils.getAvailableInfoFormat()).map( label => {
            return INFO_FORMATS[label];
        });
    },
    /**
     * @return {string} the default info format value
     */
    getDefaultInfoFormatValue() {
        return INFO_FORMATS[MapInfoUtils.AVAILABLE_FORMAT[0]];
    },
    clickedPointToGeoJson(clickedPoint) {
        if (!clickedPoint) {
            return [];
        }
        if (clickedPoint.type === "Feature") {
            let features = [pointOnSurface(clickedPoint)];
            if (clickedPoint && clickedPoint.geometry && clickedPoint.geometry.type !== "Point") {
                features.push(clickedPoint);
            }
            return features;
        }

        if (clickedPoint.lng === undefined || clickedPoint.lat === undefined) {
            return [];
        }
        return [
            {
                id: "get-feature-info-point",
                type: "Feature",
                geometry: {
                    type: 'Point',
                    coordinates: [parseFloat(clickedPoint.lng), parseFloat(clickedPoint.lat)]
                }
            }
        ];
    },
    getMarkerLayer(name, clickedMapPoint, styleName, otherParams) {
        return {
            type: 'vector',
            visibility: true,
            name: name || "GetFeatureInfo",
            styleName: styleName || "marker",
            features: MapInfoUtils.clickedPointToGeoJson(clickedMapPoint),
            ...otherParams
        };
    },
    /**
     * Returns a bounds object.
     * @param {number} minX Minimum X.
     * @param {number} minY Minimum Y.
     * @param {number} maxX Maximum X.
     * @param {number} maxY Maximum Y.
     * @return {Object} Extent.
     */
    createBBox(minX, minY, maxX, maxY) {
        return { minx: minX, miny: minY, maxx: maxX, maxy: maxY };
    },
    /**
     * Creates a bbox of size dimensions areund the center point given to it given the
     * resolution and the rotation
     * @param center {object} the x,y coordinate of the point
     * @param resolution {number} the resolution of the map
     * @param rotation {number} the optional rotation of the new bbox
     * @param size {object} width,height of the desired bbox
     * @return {object} the desired bbox {minx, miny, maxx, maxy}
     */
     getProjectedBBox(center, resolution, rotation = 0, size) {
        let dx = resolution * size[0] / 2;
        let dy = resolution * size[1] / 2;
        let cosRotation = Math.cos(rotation);
        let sinRotation = Math.sin(rotation);
        let xCos = dx * cosRotation;
        let xSin = dx * sinRotation;
        let yCos = dy * cosRotation;
        let ySin = dy * sinRotation;
        let x = center.x;
        let y = center.y;
        let x0 = x - xCos + ySin;
        let x1 = x - xCos - ySin;
        let x2 = x + xCos - ySin;
        let x3 = x + xCos + ySin;
        let y0 = y - xSin - yCos;
        let y1 = y - xSin + yCos;
        let y2 = y + xSin + yCos;
        let y3 = y + xSin - yCos;
        let bounds = MapInfoUtils.createBBox(
            Math.min(x0, x1, x2, x3), Math.min(y0, y1, y2, y3),
            Math.max(x0, x1, x2, x3), Math.max(y0, y1, y2, y3));
        return bounds;
    },
    buildIdentifyVectorRequest(layer, props) {
        return {
            request: {
                lat: props.point.latlng.lat,
                lng: props.point.latlng.lng
            },
            metadata: {
                fields: Object.keys(layer.features[0].properties),
                title: layer.name,
                resolution: props.map && props.map && props.map.zoom && MapUtils.getCurrentResolution(props.map.zoom, 0, 21, 96),
                buffer: props.buffer,
                units: props.map && props.map.units
            },
            url: ""
        };
    },
    buildIdentifyWMSRequest(layer, props) {
        /* In order to create a valid feature info request
         * we create a bbox of 101x101 pixel that wrap the point.
         * center point is repojected then is built a box of 101x101pixel around it
         */
        const heightBBox = (props && props.sizeBBox && props.sizeBBox.height) || 101;
        const widthBBox = (props && props.sizeBBox && props.sizeBBox.width) || 101;
        const size = [heightBBox, widthBBox];
        const rotation = 0;
        const resolution = MapUtils.getCurrentResolution(props.map.zoom, 0, 21, 96);
        let wrongLng = props.point.latlng.lng;
        // longitude restricted to the [-180°,+180°] range
        let lngCorrected = wrongLng - (360) * Math.floor(wrongLng / (360) + 0.5);
        const center = {x: lngCorrected, y: props.point.latlng.lat};
        let centerProjected = CoordinatesUtils.reproject(center, 'EPSG:4326', props.map.projection);
        let bounds = MapInfoUtils.getProjectedBBox(centerProjected, resolution, rotation, size, null);
        let queryLayers = layer.name;
        if (layer.queryLayers) {
            queryLayers = layer.queryLayers.join(",");
        }

        return {
            request: {
                id: layer.id,
                layers: layer.name,
                query_layers: queryLayers,
                styles: layer.style,
                x: ((widthBBox % 2) === 1) ? Math.ceil(widthBBox / 2) : widthBBox / 2,
                y: ((widthBBox % 2) === 1) ? Math.ceil(widthBBox / 2) : widthBBox / 2,
                height: heightBBox,
                width: widthBBox,
                srs: CoordinatesUtils.normalizeSRS(props.map.projection),
                bbox: bounds.minx + "," +
                      bounds.miny + "," +
                      bounds.maxx + "," +
                      bounds.maxy,
                feature_count: props.maxItems,
                info_format: props.format,
                ...assign({}, layer.baseParams, layer.params, props.params)
            },
            metadata: {
                title: layer.title,
                regex: layer.featureInfoRegex
            },
            url: isArray(layer.url) ?
                layer.url[0] :
                layer.url.replace(/[?].*$/g, '')
        };
    },
    buildIdentifyRequest(layer, props) {
        if (layer.type === 'wms') {
            return MapInfoUtils.buildIdentifyWMSRequest(layer, props);
        }
        if (layer.type === 'vector') {
            return MapInfoUtils.buildIdentifyVectorRequest(layer, props);
        }
        return {};
    },
    getValidator(format) {
        const defaultValidator = {
            getValidResponses: (responses) => responses,
            getNoValidResponses: () => []
        };
        return {
            getValidResponses: (responses) => {
                return responses.reduce((previous, current) => {
                    const valid = (FeatureInfoUtils.Validator[current.format || INFO_FORMATS_BY_MIME_TYPE[format]] || defaultValidator).getValidResponses([current]);
                    return [...previous, ...valid];
                }, []);
            },
            getNoValidResponses: (responses) => {
                return responses.reduce((previous, current) => {
                    const valid = (FeatureInfoUtils.Validator[current.format || INFO_FORMATS_BY_MIME_TYPE[format]] || defaultValidator).getNoValidResponses([current]);
                    return [...previous, ...valid];
                }, []);
            }
        };
    },
    getViewers() {
        return {
            [FeatureInfoUtils.INFO_FORMATS.JSON]: require('../components/data/identify/viewers/JSONViewer'),
            [FeatureInfoUtils.INFO_FORMATS.HTML]: require('../components/data/identify/viewers/HTMLViewer'),
            [FeatureInfoUtils.INFO_FORMATS.TEXT]: require('../components/data/identify/viewers/TextViewer')
        };
    },
    defaultQueryableFilter(l) {
        return l.visibility &&
            (l.type === 'wms' || l.type === 'vector') &&
            (l.queryable === undefined || l.queryable) &&
            l.group !== "background"
        ;
    }
};

module.exports = MapInfoUtils;
