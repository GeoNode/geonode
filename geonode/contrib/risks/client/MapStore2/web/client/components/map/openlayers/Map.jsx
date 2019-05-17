/**
 * Copyright 2015-2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var ol = require('openlayers');
var React = require('react');
var assign = require('object-assign');

var CoordinatesUtils = require('../../../utils/CoordinatesUtils');
var ConfigUtils = require('../../../utils/ConfigUtils');
var mapUtils = require('../../../utils/MapUtils');

const {isEqual, throttle} = require('lodash');

var OpenlayersMap = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        style: React.PropTypes.object,
        center: ConfigUtils.PropTypes.center,
        zoom: React.PropTypes.number.isRequired,
        mapStateSource: ConfigUtils.PropTypes.mapStateSource,
        projection: React.PropTypes.string,
        onMapViewChanges: React.PropTypes.func,
        onClick: React.PropTypes.func,
        mapOptions: React.PropTypes.object,
        zoomControl: React.PropTypes.bool,
        mousePointer: React.PropTypes.string,
        onMouseMove: React.PropTypes.func,
        onLayerLoading: React.PropTypes.func,
        onLayerLoad: React.PropTypes.func,
        onLayerError: React.PropTypes.func,
        resize: React.PropTypes.number,
        measurement: React.PropTypes.object,
        changeMeasurementState: React.PropTypes.func,
        registerHooks: React.PropTypes.bool,
        interactive: React.PropTypes.bool,
        onInvalidLayer: React.PropTypes.func,
        bbox: React.PropTypes.object
    },
    getDefaultProps() {
        return {
          id: 'map',
          onMapViewChanges: () => {},
          onInvalidLayer: () => {},
          onClick: null,
          onMouseMove: () => {},
          mapOptions: {},
          projection: 'EPSG:3857',
          onLayerLoading: () => {},
          onLayerLoad: () => {},
          onLayerError: () => {},
          resize: 0,
          registerHooks: true,
          interactive: true
        };
    },
    componentDidMount() {
        var center = CoordinatesUtils.reproject([this.props.center.x, this.props.center.y], 'EPSG:4326', this.props.projection);

        let interactionsOptions = assign(this.props.interactive ? {} : {
            doubleClickZoom: false,
            dragPan: false,
            altShiftDragRotate: false,
            keyboard: false,
            mouseWheelZoom: false,
            shiftDragZoom: false,
            pinchRotate: false,
            pinchZoom: false
        }, this.props.mapOptions.interactions);

        let interactions = ol.interaction.defaults(assign({
            dragPan: false,
            mouseWheelZoom: false
        }, interactionsOptions, {}));
        if (interactionsOptions === undefined || interactionsOptions.dragPan === undefined || interactionsOptions.dragPan) {
            interactions.extend([
                new ol.interaction.DragPan({kinetic: false})
            ]);
        }
        if (interactionsOptions === undefined || interactionsOptions.mouseWheelZoom === undefined || interactionsOptions.mouseWheelZoom) {
            interactions.extend([
                new ol.interaction.MouseWheelZoom({duration: 0})
            ]);
        }
        let controls = ol.control.defaults(assign({
            zoom: this.props.zoomControl,
            attributionOptions: ({
              collapsible: false
            })
        }, this.props.mapOptions.controls));
        let map = new ol.Map({
          layers: [],
          controls: controls,
          interactions: interactions,
          target: this.props.id,
          view: this.createView(center, Math.round(this.props.zoom), this.props.projection, this.props.mapOptions && this.props.mapOptions.view)
        });

        this.map = map;

        map.on('moveend', this.updateMapInfoState);
        map.on('singleclick', (event) => {
            if (this.props.onClick) {
                let pos = event.coordinate.slice();
                let coords = ol.proj.toLonLat(pos, this.props.projection);
                let tLng = (( coords[0] / 360) % 1) * 360;
                if (tLng < -180) {
                    tLng = tLng + 360;
                } else if (tLng > 180) {
                    tLng = tLng - 360;
                }
                this.props.onClick({
                    pixel: {
                        x: event.pixel[0],
                        y: event.pixel[1]
                    },
                    latlng: {
                        lat: coords[1],
                        lng: tLng
                    },
                    modifiers: {
                        alt: event.originalEvent.altKey,
                        ctrl: event.originalEvent.ctrlKey,
                        shift: event.originalEvent.shiftKey
                    }
                });
            }
        });
        const mouseMove = throttle(this.mouseMoveEvent, 100);
        map.on('pointermove', mouseMove);

        this.updateMapInfoState();
        this.setMousePointer(this.props.mousePointer);
        // NOTE: this re-call render function after div creation to have the map initialized.
        this.forceUpdate();

        if (this.props.registerHooks) {
            this.registerHooks();
        }
    },
    componentWillReceiveProps(newProps) {
        if (newProps.mousePointer !== this.props.mousePointer) {
            this.setMousePointer(newProps.mousePointer);
        }

        if (newProps.zoomControl !== this.props.zoomControl) {
            if (newProps.zoomControl) {
                this.map.addControl(new ol.control.Zoom());
            } else {
                this.map.removeControl(this.map.getControls().getArray().filter((ctl) => ctl instanceof ol.control.Zoom)[0]);
            }
        }

        if (this.map && this.props.id !== newProps.mapStateSource) {
            this._updateMapPositionFromNewProps(newProps);
        }

        if (this.map && newProps.resize !== this.props.resize) {
            setTimeout(() => {
                this.map.updateSize();
            }, 0);
        }

        if (this.map && ((this.props.projection !== newProps.projection) || this.haveResolutionsChanged(newProps))) {
            const center = CoordinatesUtils.reproject([
                this.props.center.x,
                this.props.center.y
            ], 'EPSG:4326', newProps.projection);
            this.map.setView(this.createView(center, newProps.zoom, newProps.projection, newProps.mapOptions && newProps.mapOptions.view));
            // We have to force ol to drop tile and reload
            this.map.getLayers().forEach((l) => {
                let source = l.getSource();
                if (source.getTileLoadFunction) {
                    source.setTileLoadFunction(source.getTileLoadFunction());
                }
            });
            this.map.render();
        }
    },
    componentWillUnmount() {
        this.map.setTarget(null);
    },
    getResolutions() {
        if (this.props.mapOptions && this.props.mapOptions.view && this.props.mapOptions.view.resolutions) {
            return this.props.mapOptions.view.resolutions;
        }
        const defaultMaxZoom = 28;
        const defaultZoomFactor = 2;

        let minZoom = this.props.mapOptions.minZoom !== undefined ?
            this.props.mapOptions.minZoom : 0;

        let maxZoom = this.props.mapOptions.maxZoom !== undefined ?
            this.props.mapOptions.maxZoom : defaultMaxZoom;

        let zoomFactor = this.props.mapOptions.zoomFactor !== undefined ?
            this.props.mapOptions.zoomFactor : defaultZoomFactor;

        const projection = this.map.getView().getProjection();
        const extent = projection.getExtent();
        const size = !extent ?
            // use an extent that can fit the whole world if need be
            360 * ol.proj.METERS_PER_UNIT[ol.proj.Units.DEGREES] /
                ol.proj.METERS_PER_UNIT[projection.getUnits()] :
            Math.max(ol.extent.getWidth(extent), ol.extent.getHeight(extent));

        const defaultMaxResolution = size / 256 / Math.pow(
            defaultZoomFactor, 0);

        const defaultMinResolution = defaultMaxResolution / Math.pow(
            defaultZoomFactor, defaultMaxZoom - 0);

        // user provided maxResolution takes precedence
        let maxResolution = this.props.mapOptions.maxResolution;
        if (maxResolution !== undefined) {
            minZoom = 0;
        } else {
            maxResolution = defaultMaxResolution / Math.pow(zoomFactor, minZoom);
        }

        // user provided minResolution takes precedence
        let minResolution = this.props.mapOptions.minResolution;
        if (minResolution === undefined) {
            if (this.props.mapOptions.maxZoom !== undefined) {
                if (this.props.mapOptions.maxResolution !== undefined) {
                    minResolution = maxResolution / Math.pow(zoomFactor, maxZoom);
                } else {
                    minResolution = defaultMaxResolution / Math.pow(zoomFactor, maxZoom);
                }
            } else {
                minResolution = defaultMinResolution;
            }
        }

        // given discrete zoom levels, minResolution may be different than provided
        maxZoom = minZoom + Math.floor(
            Math.log(maxResolution / minResolution) / Math.log(zoomFactor));
        return Array.apply(0, Array(maxZoom - minZoom + 1)).map((x, y) => maxResolution / Math.pow(zoomFactor, y));
    },
    render() {
        const map = this.map;
        const children = map ? React.Children.map(this.props.children, child => {
            return child ? React.cloneElement(child, {
                map: map,
                mapId: this.props.id,
                onLayerLoading: this.props.onLayerLoading,
                onLayerError: this.props.onLayerError,
                onLayerLoad: this.props.onLayerLoad,
                projection: this.props.projection,
                onInvalid: this.props.onInvalidLayer
            }) : null;
        }) : null;

        return (
            <div id={this.props.id} style={this.props.style}>
                {children}
            </div>
        );
    },
    mouseMoveEvent(event) {
        if (!event.dragging && event.coordinate) {
            let pos = event.coordinate.slice();
            let coords = ol.proj.toLonLat(pos, this.props.projection);
            let tLng = (( coords[0] / 360) % 1) * 360;
            if (tLng < -180) {
                tLng = tLng + 360;
            } else if (tLng > 180) {
                tLng = tLng - 360;
            }
            this.props.onMouseMove({
                y: coords[1] || 0.0,
                x: tLng || 0.0,
                crs: "EPSG:4326",
                pixel: {
                    x: event.pixel[0],
                    y: event.pixel[1]
                }
            });
        }
    },
    updateMapInfoState() {
        let view = this.map.getView();
        let c = this.normalizeCenter(view.getCenter());
        let bbox = view.calculateExtent(this.map.getSize());
        let size = {
            width: this.map.getSize()[0],
            height: this.map.getSize()[1]
        };
        this.props.onMapViewChanges({x: c[0] || 0.0, y: c[1] || 0.0, crs: 'EPSG:4326'}, view.getZoom(), {
            bounds: {
                minx: bbox[0],
                miny: bbox[1],
                maxx: bbox[2],
                maxy: bbox[3]
            },
            crs: view.getProjection().getCode(),
            rotation: view.getRotation()
        }, size, this.props.id, this.props.projection);
    },
    haveResolutionsChanged(newProps) {
        const resolutions = this.props.mapOptions && this.props.mapOptions.view ? this.props.mapOptions.view.resolutions : undefined;
        const newResolutions = newProps.mapOptions && newProps.mapOptions.view ? newProps.mapOptions.view.resolutions : undefined;
        return !isEqual(resolutions, newResolutions);
    },
    createView(center, zoom, projection, options) {
        const viewOptions = assign({}, {
            projection: projection,
            center: [center.x, center.y],
            zoom: zoom
        }, options || {});
        return new ol.View(viewOptions);
    },
    _updateMapPositionFromNewProps(newProps) {
        var view = this.map.getView();
        const currentCenter = this.props.center;
        const centerIsUpdated = newProps.center.y === currentCenter.y &&
                               newProps.center.x === currentCenter.x;

        if (!centerIsUpdated) {
            // let center = ol.proj.transform([newProps.center.x, newProps.center.y], 'EPSG:4326', newProps.projection);
            let center = CoordinatesUtils.reproject({x: newProps.center.x, y: newProps.center.y}, 'EPSG:4326', newProps.projection, true);
            view.setCenter([center.x, center.y]);
        }
        if (Math.round(newProps.zoom) !== this.props.zoom) {
            view.setZoom(Math.round(newProps.zoom));
        }
        if (newProps.bbox && newProps.bbox.rotation !== undefined && newProps.bbox.rotation !== this.props.bbox.rotation) {
            view.setRotation(newProps.bbox.rotation);
        }
    },
    normalizeCenter: function(center) {
        let c = CoordinatesUtils.reproject({x: center[0], y: center[1]}, this.props.projection, 'EPSG:4326', true);
        return [c.x, c.y];
    },
    setMousePointer(pointer) {
        if (this.map) {
            const mapDiv = this.map.getViewport();
            mapDiv.style.cursor = pointer || 'auto';
        }
    },
    registerHooks() {
        mapUtils.registerHook(mapUtils.RESOLUTIONS_HOOK, () => {
            return this.getResolutions();
        });
        mapUtils.registerHook(mapUtils.RESOLUTION_HOOK, () => {
            return this.map.getView().getResolution();
        });
        mapUtils.registerHook(mapUtils.COMPUTE_BBOX_HOOK, (center, zoom) => {
            var olCenter = CoordinatesUtils.reproject([center.x, center.y], 'EPSG:4326', this.props.projection);
            let view = this.createView(olCenter, zoom, this.props.projection, this.props.mapOptions && this.props.mapOptions.view);
            let size = this.map.getSize();
            let bbox = view.calculateExtent(size);
            return {
                bounds: {
                    minx: bbox[0],
                    miny: bbox[1],
                    maxx: bbox[2],
                    maxy: bbox[3]
                },
                crs: this.props.projection,
                rotation: this.map.getView().getRotation()
            };
        });
        mapUtils.registerHook(mapUtils.GET_PIXEL_FROM_COORDINATES_HOOK, (pos) => {
            return this.map.getPixelFromCoordinate(pos);
        });
        mapUtils.registerHook(mapUtils.GET_COORDINATES_FROM_PIXEL_HOOK, (pixel) => {
            return this.map.getCoordinateFromPixel(pixel);
        });
    }
});
// add overrides for css
require('./mapstore-ol-overrides.css');
module.exports = OpenlayersMap;
