/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
var L = require('leaflet');
require('leaflet-draw');

const CoordinatesUtils = require('../../../utils/CoordinatesUtils');

const DrawSupport = React.createClass({
    propTypes: {
        map: React.PropTypes.object,
        drawOwner: React.PropTypes.string,
        drawStatus: React.PropTypes.string,
        drawMethod: React.PropTypes.string,
        features: React.PropTypes.array,
        onChangeDrawingStatus: React.PropTypes.func,
        onEndDrawing: React.PropTypes.func,
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            map: null,
            drawOwner: null,
            drawStatus: null,
            drawMethod: null,
            features: null,
            onChangeDrawingStatus: () => {},
            onEndDrawing: () => {}
        };
    },
    componentWillReceiveProps(newProps) {
        let drawingStrings = this.props.messages || (this.context.messages) ? this.context.messages.drawLocal : false;
        if (drawingStrings) {
            L.drawLocal = drawingStrings;
        }
        if (this.props.drawStatus !== newProps.drawStatus || newProps.drawStatus === "replace" || this.props.drawMethod !== newProps.drawMethod) {
            switch (newProps.drawStatus) {
                case ("create"):
                    this.addLayer(newProps);
                    break;
                case ("start"):
                    this.addDrawInteraction(newProps);
                    break;
                case ("stop"):
                    this.removeDrawInteraction();
                    break;
                case ("replace"):
                    this.replaceFeatures(newProps);
                    break;
                case ("clean"):
                    this.clean();
                    break;
                default :
                    return;
            }
        }
    },
    onDraw: {
        drawStart() {
            this.drawing = true;
        },
        created(evt) {
            this.drawing = false;
            const layer = evt.layer;
            // let drawn geom stay on the map
            let geoJesonFt = layer.toGeoJSON();
            let bounds = layer.getBounds();
            let extent = this.boundsToOLExtent(layer.getBounds());
            let center = bounds.getCenter();
            center = [center.lng, center.lat];
            let radius = layer.getRadius ? layer.getRadius() : 0;
            let coordinates = geoJesonFt.geometry.coordinates;
            let projection = "EPSG:4326";
            let type = geoJesonFt.geometry.type;
            if (evt.layerType === "circle") {
                // Circle needs to generate path and needs to be projected before
                // When GeometryDetails update circle it's in charge to generete path
                // but for first time we need to do this!
                geoJesonFt.projection = "EPSG:4326";
                projection = "EPSG:900913";
                extent = CoordinatesUtils.reprojectBbox(extent, "EPSG:4326", projection);
                center = CoordinatesUtils.reproject(center, "EPSG:4326", projection);
                geoJesonFt.radius = radius;
                coordinates = CoordinatesUtils.calculateCircleCoordinates(center, radius, 100);
                center = [center.x, center.y];
                type = "Polygon";
            }
            // We always draw geoJson feature
            this.drawLayer.addData(geoJesonFt);
            // Geometry respect query form panel needs
            let geometry = {
                type: type,
                extent: extent,
                center: center,
                coordinates: coordinates,
                radius: radius,
                projection: projection
            };

            this.props.onChangeDrawingStatus('stop', this.props.drawMethod, this.props.drawOwner);
            this.props.onEndDrawing(geometry, this.props.drawOwner);
        }
    },
    render() {
        return null;
    },
    addLayer: function(newProps) {
        this.clean();

        let vector = L.geoJson(null, {
            pointToLayer: function(feature, latLng) {
                let center = CoordinatesUtils.reproject({x: latLng.lng, y: latLng.lat}, feature.projection, "EPSG:4326");
                return L.circle(L.latLng(center.y, center.x), feature.radius);
            },
             style: {
                    color: '#ffcc33',
                    opacity: 1,
                    weight: 3,
                    fillColor: '#ffffff',
                    fillOpacity: 0.2,
                    clickable: false
            }
        });
        this.props.map.addLayer(vector);
        // Immidiatly draw passed features
        if (newProps.features && newProps.features.length > 0) {

            vector.addData(this.convertFeaturesPolygonToPoint(newProps.features, this.props.drawMethod));
        }
        this.drawLayer = vector;
    },
    replaceFeatures: function(newProps) {
        if (!this.drawLayer) {
            this.addLayer(newProps);
        } else {
            this.drawLayer.clearLayers();
            this.drawLayer.addData(this.convertFeaturesPolygonToPoint(newProps.features, this.props.drawMethod));
        }
    },
    addDrawInteraction: function(newProps) {
        if (!this.drawLayer) {
            this.addLayer(newProps);
        }else {
            this.drawLayer.clearLayers();
            if (newProps.features && newProps.features.length > 0) {
                this.drawLayer.addData(this.convertFeaturesPolygonToPoint(newProps.features, this.props.drawMethod));
            }
        }

        this.removeDrawInteraction();

        this.props.map.on('draw:created', this.onDraw.created, this);
        this.props.map.on('draw:drawstart', this.onDraw.drawStart, this);

        if (newProps.drawMethod === 'LineString' ||
                newProps.drawMethod === 'Bearing') {
            this.drawControl = new L.Draw.Polyline(this.props.map, {
                shapeOptions: {
                    color: '#000000',
                    weight: 2,
                    fillColor: '#ffffff',
                    fillOpacity: 0.2
                },
                repeatMode: true
            });
        } else if (newProps.drawMethod === 'Polygon') {
            this.drawControl = new L.Draw.Polygon(this.props.map, {
                shapeOptions: {
                    color: '#000000',
                    weight: 2,
                    fillColor: '#ffffff',
                    fillOpacity: 0.2,
                    dashArray: [5, 5],
                    guidelineDistance: 5
                },
                repeatMode: true
            });
        } else if (newProps.drawMethod === 'BBOX') {
            this.drawControl = new L.Draw.Rectangle(this.props.map, {
                draw: false,
                shapeOptions: {
                    color: '#000000',
                    weight: 2,
                    fillColor: '#ffffff',
                    fillOpacity: 0.2,
                    dashArray: [5, 5]
                },
                repeatMode: true
            });
        } else if (newProps.drawMethod === 'Circle') {
            this.drawControl = new L.Draw.Circle(this.props.map, {
                shapeOptions: {
                    color: '#000000',
                    weight: 2,
                    fillColor: '#ffffff',
                    fillOpacity: 0.2,
                    dashArray: [5, 5]
                },
                repeatMode: true
            });
        }

        // start the draw control
        this.drawControl.enable();
    },
    removeDrawInteraction: function() {
        if (this.drawControl !== null && this.drawControl !== undefined) {
            // Needed if missin disable() isn't warking
            this.drawControl.setOptions({repeatMode: false});
            this.drawControl.disable();
            this.drawControl = null;
            this.props.map.off('draw:created', this.onDraw.created, this);
            this.props.map.off('draw:drawstart', this.onDraw.drawStart, this);
        }
    },
    clean: function() {
        this.removeDrawInteraction();

        if (this.drawLayer) {
            this.drawLayer.clearLayers();
            this.props.map.removeLayer(this.drawLayer);
            this.drawLayer = null;
        }
    },
    boundsToOLExtent: function(bounds) {
        return [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()];
    },
    convertFeaturesPolygonToPoint(features, method) {
        return method === 'Circle' ? features.map((f) => {
            return {...f, type: "Point"};
        }) : features;

    }
});

module.exports = DrawSupport;
