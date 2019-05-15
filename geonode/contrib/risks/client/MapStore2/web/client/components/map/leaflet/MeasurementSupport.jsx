/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const assign = require('object-assign');
var L = require('leaflet');
const {slice} = require('lodash');
var CoordinatesUtils = require('../../../utils/CoordinatesUtils');

require('leaflet-draw');

const MeasurementSupport = React.createClass({
    propTypes: {
        map: React.PropTypes.object,
        metric: React.PropTypes.bool,
        feet: React.PropTypes.bool,
        projection: React.PropTypes.string,
        measurement: React.PropTypes.object,
        changeMeasurementState: React.PropTypes.func,
        messages: React.PropTypes.object,
        updateOnMouseMove: React.PropTypes.bool
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            updateOnMouseMove: false
        };
    },
    componentWillReceiveProps(newProps) {
        if (newProps.measurement.geomType && newProps.measurement.geomType !== this.props.measurement.geomType ) {
            this.addDrawInteraction(newProps);
        }

        if (!newProps.measurement.geomType) {
            this.removeDrawInteraction();
        }
    },
    onDraw: {
        drawStart() {
            this.drawing = true;
        },
        created(evt) {
            this.drawing = false;
            // let drawn geom stay on the map
            this.props.map.addLayer(evt.layer);
            // preserve the currently created layer to remove it later on
            this.lastLayer = evt.layer;

            if (this.props.measurement.geomType === 'Point') {
                let pos = this.drawControl._markers.getLatLng();
                let point = {x: pos.lng, y: pos.lat, srs: 'EPSG:4326'};
                let newMeasureState = assign({}, this.props.measurement, {point: point});
                this.props.changeMeasurementState(newMeasureState);
            }
        }
    },
    render() {
        // moved here the translations because when language changes it is forced a render of this component. (see connect of measure plugin)
        var drawingStrings = this.props.messages || (this.context.messages ? this.context.messages.drawLocal : false);
        if (drawingStrings) {
            L.drawLocal = drawingStrings;
        }

        return null;
    },
    updateMeasurementResults() {
        if (!this.drawing || !this.drawControl) {
            return;
        }
        let distance = 0;
        let area = 0;
        let bearing = 0;

        let currentLatLng = this.drawControl._currentLatLng;
        if (this.props.measurement.geomType === 'LineString' && this.drawControl._markers && this.drawControl._markers.length > 0) {
            // calculate length
            let previousLatLng = this.drawControl._markers[this.drawControl._markers.length - 1].getLatLng();
            distance = this.drawControl._measurementRunningTotal + currentLatLng.distanceTo(previousLatLng);
        } else if (this.props.measurement.geomType === 'Polygon' && this.drawControl._poly) {
            // calculate area
            let latLngs = [...this.drawControl._poly.getLatLngs(), currentLatLng];
            area = L.GeometryUtil.geodesicArea(latLngs);
        } else if (this.props.measurement.geomType === 'Bearing' && this.drawControl._markers && this.drawControl._markers.length > 0) {
            // calculate bearing
            let bearingMarkers = this.drawControl._markers;
            let coords1 = [bearingMarkers[0].getLatLng().lng, bearingMarkers[0].getLatLng().lat];
            let coords2;
            if (bearingMarkers.length === 1) {
                coords2 = [currentLatLng.lng, currentLatLng.lat];
            } else if (bearingMarkers.length === 2) {
                coords2 = [bearingMarkers[1].getLatLng().lng, bearingMarkers[1].getLatLng().lat];
            }
            // in order to align the results between leaflet and openlayers the coords are repojected only for leaflet
            coords1 = CoordinatesUtils.reproject(coords1, 'EPSG:4326', this.props.projection);
            coords2 = CoordinatesUtils.reproject(coords2, 'EPSG:4326', this.props.projection);
            // calculate the azimuth as base for bearing information
            bearing = CoordinatesUtils.calculateAzimuth(coords1, coords2, this.props.projection);
        }

        let newMeasureState = assign({}, this.props.measurement,
            {
                point: null, // Point is set in onDraw.created
                len: distance,
                area: area,
                bearing: bearing
            }
        );
        this.props.changeMeasurementState(newMeasureState);
    },
    mapClickHandler: function() {
        if (!this.drawing && this.drawControl !== null) {
            // re-enable draw control, since it is stopped after
            // every finished sketch
            this.props.map.removeLayer(this.lastLayer);
            this.drawControl.enable();
            this.drawing = true;
        } else {
            let bearingMarkers = this.drawControl._markers || [];

            if (this.props.measurement.geomType === 'Bearing' && bearingMarkers.length >= 2) {
                this.drawControl._markers = slice(this.drawControl._markers, 0, 2);
                this.drawControl._poly._latlngs = slice(this.drawControl._poly._latlngs, 0, 2);
                this.drawControl._poly._originalPoints = slice(this.drawControl._poly._originalPoints, 0, 2);
                this.updateMeasurementResults();
                this.drawControl._finishShape();
                this.drawControl.disable();
            } else {
                this.updateMeasurementResults();
            }
        }
    },
    addDrawInteraction: function(newProps) {

        this.removeDrawInteraction();

        this.props.map.on('draw:created', this.onDraw.created, this);
        this.props.map.on('draw:drawstart', this.onDraw.drawStart, this);
        this.props.map.on('click', this.mapClickHandler, this);
        if (this.props.updateOnMouseMove) {
            this.props.map.on('mousemove', this.updateMeasurementResults, this);
        }

        if (newProps.measurement.geomType === 'Point') {
            this.drawControl = new L.Draw.Marker(this.props.map, {
                repeatMode: false
            });
        } else if (newProps.measurement.geomType === 'LineString' ||
                newProps.measurement.geomType === 'Bearing') {
            this.drawControl = new L.Draw.Polyline(this.props.map, {
                shapeOptions: {
                    color: '#ffcc33',
                    weight: 2
                },
                metric: this.props.metric,
                feet: this.props.feet,
                repeatMode: false
            });
        } else if (newProps.measurement.geomType === 'Polygon') {
            this.drawControl = new L.Draw.Polygon(this.props.map, {
                shapeOptions: {
                    color: '#ffcc33',
                    weight: 2,
                    fill: 'rgba(255, 255, 255, 0.2)'
                },
                repeatMode: false
            });
        }

        // start the draw control
        this.drawControl.enable();
    },
    removeDrawInteraction: function() {
        if (this.drawControl !== null && this.drawControl !== undefined) {
            this.drawControl.disable();
            this.drawControl = null;
            if (this.lastLayer) {
                this.props.map.removeLayer(this.lastLayer);
            }
            this.props.map.off('draw:created', this.onDraw.created, this);
            this.props.map.off('draw:drawstart', this.onDraw.drawStart, this);
            this.props.map.off('click', this.mapClickHandler, this);
            if (this.props.updateOnMouseMove) {
                this.props.map.off('mousemove', this.updateMeasurementResults, this);
            }
        }
    }
});

module.exports = MeasurementSupport;
