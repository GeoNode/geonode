/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const ol = require('openlayers');

const assign = require('object-assign');

const DrawSupport = React.createClass({
    propTypes: {
        map: React.PropTypes.object,
        drawOwner: React.PropTypes.string,
        drawStatus: React.PropTypes.string,
        drawMethod: React.PropTypes.string,
        features: React.PropTypes.array,
        onChangeDrawingStatus: React.PropTypes.func,
        onEndDrawing: React.PropTypes.func
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
    },
    render() {
        return null;
    },
    addLayer: function(newProps) {
        var source;
        var vector;
        this.geojson = new ol.format.GeoJSON();

        // create a layer to draw on
        source = new ol.source.Vector();
        vector = new ol.layer.Vector({
            source: source,
            zIndex: 1000000,
            style: new ol.style.Style({
                fill: new ol.style.Fill({
                    color: 'rgba(255, 255, 255, 0.2)'
                }),
                stroke: new ol.style.Stroke({
                    color: '#ffcc33',
                  width: 2
                }),
                image: new ol.style.Circle({
                    radius: 7,
                    fill: new ol.style.Fill({
                        color: '#ffcc33'
                    })
                })
            })
        });

        this.props.map.addLayer(vector);

        if (newProps.features && newProps.features > 0) {
            for (let i = 0; i < newProps.features.length; i++) {
                let feature = newProps.features[i];
                if (!(feature instanceof Object)) {
                    feature = this.geojson.readFeature(newProps.feature);
                }

                source.addFeature(feature);
            }
        }

        this.drawSource = source;
        this.drawLayer = vector;
    },
    replaceFeatures: function(newProps) {
        if (!this.drawLayer) {
            this.addLayer(newProps);
        } else {
            this.drawSource.clear();
            newProps.features.map((geom) => {
                let geometry = geom.radius && geom.center ?
                    ol.geom.Polygon.fromCircle(new ol.geom.Circle([geom.center.x, geom.center.y], geom.radius), 100) : new ol.geom.Polygon(geom.coordinates);

                let feature = new ol.Feature({
                    geometry: geometry
                });

                this.drawSource.addFeature(feature);
            });
        }
    },
    addDrawInteraction: function(newProps) {
        let draw;
        let geometryType = newProps.drawMethod;

        if (!this.drawLayer) {
            this.addLayer(newProps);
        }

        if (this.drawInteraction) {
            this.removeDrawInteraction();
        }

        let drawBaseProps = {
            source: this.drawSource,
            type: /** @type {ol.geom.GeometryType} */ geometryType,
            style: new ol.style.Style({
                fill: new ol.style.Fill({
                    color: 'rgba(255, 255, 255, 0.2)'
                }),
                stroke: new ol.style.Stroke({
                    color: 'rgba(0, 0, 0, 0.5)',
                    lineDash: [10, 10],
                    width: 2
                }),
                image: new ol.style.Circle({
                    radius: 5,
                    stroke: new ol.style.Stroke({
                        color: 'rgba(0, 0, 0, 0.7)'
                    }),
                    fill: new ol.style.Fill({
                        color: 'rgba(255, 255, 255, 0.2)'
                    })
                })
            }),
            condition: ol.events.condition.always
        };

        // Prepare the properties for the BBOX drawing
        let roiProps = {};
        if (geometryType === "BBOX") {
            roiProps.type = "LineString";
            roiProps.maxPoints = 2;
            roiProps.geometryFunction = function(coordinates, geometry) {
                let geom = geometry;
                if (!geom) {
                    geom = new ol.geom.Polygon(null);
                }

                let start = coordinates[0];
                let end = coordinates[1];
                geom.setCoordinates([
                  [start, [start[0], end[1]], end, [end[0], start[1]], start]
                ]);

                return geom;
            };
        } else if (geometryType === "Circle") {
            roiProps.maxPoints = 100;
            roiProps.geometryFunction = ol.interaction.Draw.createRegularPolygon(roiProps.maxPoints);
        }

        let drawProps = assign({}, drawBaseProps, roiProps);

        // create an interaction to draw with
        draw = new ol.interaction.Draw(drawProps);

        draw.on('drawstart', function(evt) {
            this.sketchFeature = evt.feature;
            this.drawSource.clear();
        }, this);

        draw.on('drawend', function(evt) {
            this.sketchFeature = evt.feature;
            let drawnGeometry = this.sketchFeature.getGeometry();

            let extent = drawnGeometry.getExtent();
            let center = ol.extent.getCenter(drawnGeometry.getExtent());
            let coordinates = drawnGeometry.getCoordinates();
            let radius = Math.sqrt(Math.pow(center[0] - coordinates[0][0][0], 2) + Math.pow(center[1] - coordinates[0][0][1], 2));

            let geometry = {
                type: drawnGeometry.getType(),
                extent: extent,
                center: center,
                coordinates: coordinates,
                radius: radius,
                projection: this.props.map.getView().getProjection().getCode()
            };

            this.props.onEndDrawing(geometry, this.props.drawOwner);
            this.props.onChangeDrawingStatus('stop', this.props.drawMethod, this.props.drawOwner);
        }, this);

        this.props.map.addInteraction(draw);
        this.drawInteraction = draw;
        this.drawSource.clear();
    },
    removeDrawInteraction: function() {
        if (this.drawInteraction !== null) {
            this.props.map.removeInteraction(this.drawInteraction);
            this.drawInteraction = null;
            this.sketchFeature = null;
        }
    },
    clean: function() {
        this.removeDrawInteraction();

        if (this.drawLayer) {
            this.props.map.removeLayer(this.drawLayer);
            this.geojson = null;
            this.drawLayer = null;
            this.drawSource = null;
        }
    }
});

module.exports = DrawSupport;
