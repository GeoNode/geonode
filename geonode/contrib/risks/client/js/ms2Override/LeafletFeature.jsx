/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var {connect} = require('react-redux');
var L = require('leaflet');
const {isEqual} = require('lodash');
const assign = require('object-assign');
const {clickOnMap} = require('../../MapStore2/web/client/actions/map');
const {zoomInOut} = require('../actions/disaster');
var coordsToLatLngF = function(coords) {
    return new L.LatLng(coords[1], coords[0], coords[2]);
};

var coordsToLatLngs = function(coords, levelsDeep, coordsToLatLng) {
    var latlngs = [];
    var len = coords.length;
    for (let i = 0, latlng; i < len; i++) {
        latlng = levelsDeep ?
                coordsToLatLngs(coords[i], levelsDeep - 1, coordsToLatLng) :
                (coordsToLatLng || this.coordsToLatLng)(coords[i]);

        latlngs.push(latlng);
    }

    return latlngs;
};
// Create a new Leaflet layer with custom icon marker or circleMarker
var getPointLayer = function(pointToLayer, geojson, latlng, options) {
    if (pointToLayer) {
        return pointToLayer(geojson, latlng);
    }
    if (options && options.style && options.style.iconUrl) {
        return L.marker(
            latlng,
            {
                icon: L.icon({
                    iconUrl: options.style.iconUrl,
                    shadowUrl: options.style.shadowUrl,
                    iconSize: options.style.iconSize,
                    shadowSize: options.style.shadowSize,
                    iconAnchor: options.style.iconAnchor,
                    shadowAnchor: options.style.shadowAnchor,
                    popupAnchor: options.style.popupAnchor
                })
            });
    }
    return L.marker(latlng);
};

var geometryToLayer = function(geojson, options) {

    var geometry = geojson.type === 'Feature' ? geojson.geometry : geojson;
    var coords = geometry ? geometry.coordinates : null;
    var layers = [];
    var pointToLayer = options && options.pointToLayer;
    var latlng;
    var latlngs;
    var i;
    var len;
    let coordsToLatLng = options && options.coordsToLatLng || coordsToLatLngF;

    if (!coords && !geometry) {
        return null;
    }
    let layer;
    switch (geometry.type) {
    case 'Point':
        latlng = coordsToLatLng(coords);
        layer = getPointLayer(pointToLayer, geojson, latlng, options);
        layer.msId = geojson.id;
        return layer;
    case 'MultiPoint':
        for (i = 0, len = coords.length; i < len; i++) {
            latlng = coordsToLatLng(coords[i]);
            layer = getPointLayer(pointToLayer, geojson, latlng, options);
            layer.msId = geojson.id;
            layers.push(layer);
        }
        return new L.FeatureGroup(layers);

    case 'LineString':
        latlngs = coordsToLatLngs(coords, geometry.type === 'LineString' ? 0 : 1, coordsToLatLng);
        layer = new L.Polyline(latlngs, options.style);
        layer.msId = geojson.id;
        return layer;
    case 'MultiLineString':
        latlngs = coordsToLatLngs(coords, geometry.type === 'LineString' ? 0 : 1, coordsToLatLng);
        for (i = 0, len = latlngs.length; i < len; i++) {
            layer = new L.Polyline(latlngs[i], options.style);
            layer.msId = geojson.id;
            if (layer) {
                layers.push(layer);
            }
        }
        return new L.FeatureGroup(layers);
    case 'Polygon':
        latlngs = coordsToLatLngs(coords, geometry.type === 'Polygon' ? 1 : 2, coordsToLatLng);
        layer = new L.Polygon(latlngs, options.style);
        layer.msId = geojson.id;
        return layer;
    case 'MultiPolygon':
        latlngs = coordsToLatLngs(coords, geometry.type === 'Polygon' ? 1 : 2, coordsToLatLng);
        for (i = 0, len = latlngs.length; i < len; i++) {
            layer = new L.Polygon(latlngs[i], options.style);
            layer.msId = geojson.id;
            if (layer) {
                layers.push(layer);
            }
        }
        return new L.FeatureGroup(layers);
    case 'GeometryCollection':
        for (i = 0, len = geometry.geometries.length; i < len; i++) {
            layer = geometryToLayer({
                geometry: geometry.geometries[i],
                type: 'Feature',
                properties: geojson.properties
            }, options);

            if (layer) {
                layers.push(layer);
            }
        }
        return new L.FeatureGroup(layers);

    default:
        throw new Error('Invalid GeoJSON object.');
    }
};

let Feature = React.createClass({
    propTypes: {
        msId: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.number]),
        type: React.PropTypes.string,
        styleName: React.PropTypes.string,
        properties: React.PropTypes.object,
        container: React.PropTypes.object, // TODO it must be a L.GeoJSON
        geometry: React.PropTypes.object, // TODO check for geojson format for geometry
        style: React.PropTypes.object,
        onClick: React.PropTypes.func,
        clickOnMap: React.PropTypes.func,
        getFeatureInfoEnabled: React.PropTypes.bool
    },
    componentDidMount() {
        if (this.props.container) {
            this._tooltip = L.popup({closeButton: false, offset: [85, 35], className: 'disaster-map-tooltip', autoPan: false});
            let style = assign({className: this.props.getFeatureInfoEnabled && "admin" || "adminZoom"}, this.props.style);
            this._layer = geometryToLayer({
                type: this.props.type,
                geometry: this.props.geometry,
                id: this.props.msId
            }, {
                style: style,
                pointToLayer: this.props.styleName !== "marker" ? function(feature, latlng) {
                    return L.circleMarker(latlng, style || {
                        radius: 5,
                        color: "red",
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0
                    });
                } : null
            }
            );
            this.props.container.addLayer(this._layer);
            if (this.props.getFeatureInfoEnabled) {
                this._layer.on('click', (event) => {
                    if (this.props.clickOnMap) {
                        this.props.clickOnMap({
                            pixel: event.containerPoint,
                            latlng: event.latlng
                        });
                    }
                });
            } else {
                this.addEvents();
            }
        }
    },
    componentWillReceiveProps(newProps) {
        if (!isEqual(newProps.properties, this.props.properties) || !isEqual(newProps.geometry, this.props.geometry) || newProps.getFeatureInfoEnabled !== this.props.getFeatureInfoEnabled) {
            this.removeEvents();
            this.props.container.removeLayer(this._layer);
            let style = assign({className: newProps.getFeatureInfoEnabled && "admin" || "adminZoom"}, newProps.style);
            this._layer = geometryToLayer({
                type: newProps.type,
                geometry: newProps.geometry,
                id: this.props.msId
            }, {
                style: style,
                pointToLayer: newProps.styleName !== "marker" ? function(feature, latlng) {
                    return L.circleMarker(latlng, newProps.style || {
                        radius: 5,
                        color: "red",
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0
                    });
                } : null
            }
            );
            newProps.container.addLayer(this._layer);
            if ( newProps.getFeatureInfoEnabled) {
                this._layer.on('click', (event) => {
                    if (this.props.clickOnMap) {
                        this.props.clickOnMap({
                            pixel: event.containerPoint,
                            latlng: event.latlng
                        });
                    }
                });
            } else {
                this.addEvents();
            }
        }
    },
    shouldComponentUpdate(nextProps) {
        return !isEqual(nextProps.properties, this.props.properties) || !isEqual(nextProps.geometry, this.props.geometry);
    },
    componentWillUnmount() {
        if (this._layer) {
            this.props.container.removeLayer(this._layer);
        }
    },
    onClick() {
        const {properties, onClick, getFeatureInfoEnabled} = this.props;
        if (onClick && !getFeatureInfoEnabled) {
            onClick(properties.href, properties.geom);
        }
    },
    onOver(event) {
        this._layer.setStyle({weight: 4, 'className': "admin"});
        this._tooltip.setLatLng(event.latlng)
            .setContent(`Zoom to ${this.props.properties && this.props.properties.label}`);
        this._layer.addLayer(this._tooltip);
    },
    onMousemove(event) {
        this._tooltip.setLatLng(event.latlng);
    },
    onOut() {
        this._layer.removeLayer(this._tooltip);
        this._layer.setStyle({weight: 1, 'className': null});
    },
    render() {
        return null;
    },
    addEvents() {
        this._layer.on('click', this.onClick);
        this._layer.on('mouseover', this.onOver);
        this._layer.on('mouseout', this.onOut);
        this._layer.on('mousemove', this.onMousemove);
    },
    removeEvents() {
        this._layer.off('click', this.onClick);
        this._layer.off('mouseover', this.onOver);
        this._layer.off('mouseout', this.onOut);
        this._layer.off('mousemove', this.onMousemove);
    }
});

module.exports = connect((state)=> ({getFeatureInfoEnabled: state.controls && state.controls.info && state.controls.info.enabled }), {onClick: zoomInOut, clickOnMap})(Feature);
