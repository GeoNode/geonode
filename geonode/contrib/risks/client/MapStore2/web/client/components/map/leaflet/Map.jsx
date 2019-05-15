/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var L = require('leaflet');
var React = require('react');
var ConfigUtils = require('../../../utils/ConfigUtils');
var CoordinatesUtils = require('../../../utils/CoordinatesUtils');
var assign = require('object-assign');
var mapUtils = require('../../../utils/MapUtils');

const {throttle} = require('lodash');

require('./SingleClick');
let LeafletMap = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        center: ConfigUtils.PropTypes.center,
        zoom: React.PropTypes.number.isRequired,
        mapStateSource: ConfigUtils.PropTypes.mapStateSource,
        style: React.PropTypes.object,
        projection: React.PropTypes.string,
        onMapViewChanges: React.PropTypes.func,
        onClick: React.PropTypes.func,
        onRightClick: React.PropTypes.func,
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
        resolutions: React.PropTypes.array,
        onInvalidLayer: React.PropTypes.func
    },
    getDefaultProps() {
        return {
          id: 'map',
          onMapViewChanges: () => {},
          onInvalidLayer: () => {},
          onClick: null,
          onMouseMove: () => {},
          zoomControl: true,
          mapOptions: {
              zoomAnimation: true,
              attributionControl: true
          },
          projection: "EPSG:3857",
          onLayerLoading: () => {},
          onLayerLoad: () => {},
          onLayerError: () => {},
          resize: 0,
          registerHooks: true,
          style: {},
          interactive: true,
          resolutions: mapUtils.getGoogleMercatorResolutions(0, 23)
        };
    },
    getInitialState() {
        return { };
    },
    componentWillMount() {
        this.zoomOffset = 0;
        if (this.props.mapOptions && this.props.mapOptions.view && this.props.mapOptions.view.resolutions && this.props.mapOptions.view.resolutions.length > 0) {
            const scaleFun = L.CRS.EPSG3857.scale;
            const ratio = this.props.mapOptions.view.resolutions[0] / mapUtils.getGoogleMercatorResolutions(0, 23)[0];
            this.crs = assign({}, L.CRS.EPSG3857, {
                scale: (zoom) => {
                    return scaleFun.call(L.CRS.EPSG3857, zoom) / Math.pow(2, Math.round(Math.log2(ratio)));
                }
            });
            this.zoomOffset = Math.round(Math.log2(ratio));
        }
    },
    componentDidMount() {
        let mapOptions = assign({}, this.props.interactive ? {} : {
            dragging: false,
            touchZoom: false,
            scrollWheelZoom: false,
            doubleClickZoom: false,
            boxZoom: false,
            tap: false
        }, this.props.mapOptions, this.crs ? {crs: this.crs} : {});

        const map = L.map(this.props.id, assign({zoomControl: this.props.zoomControl}, mapOptions) ).setView([this.props.center.y, this.props.center.x],
          Math.round(this.props.zoom));

        this.map = map;


        this.map.on('moveend', this.updateMapInfoState);
        // this uses the hook defined in ./SingleClick.js for leaflet 0.7.*
        this.map.on('singleclick', (event) => {
            if (this.props.onClick) {
                this.props.onClick({
                    pixel: {
                        x: event.containerPoint.x,
                        y: event.containerPoint.y
                    },
                    latlng: {
                        lat: event.latlng.lat,
                        lng: event.latlng.lng
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
        this.map.on('dragstart', () => { this.map.off('mousemove', mouseMove); });
        this.map.on('dragend', () => { this.map.on('mousemove', mouseMove); });
        this.map.on('mousemove', mouseMove);
        this.map.on('contextmenu', () => {
            if (this.props.onRightClick) {
                this.props.onRightClick(event.containerPoint);
            }
        });

        this.updateMapInfoState();
        this.setMousePointer(this.props.mousePointer);
        // NOTE: this re-call render function after div creation to have the map initialized.
        this.forceUpdate();

        this.map.on('layeradd', (event) => {
            // avoid binding if not possible, e.g. for measurement vector layers
            if (!event.layer.layerId) {
                return;
            }
            if (event.layer && event.layer.options && event.layer.options.msLayer === 'vector') {
                return;
            }

            if (event && event.layer && event.layer.on ) {
                // TODO check event.layer.on is a function
                // Needed to fix GeoJSON Layer neverending loading
                let hadError = false;
                if (!(event.layer.options && event.layer.options.hideLoading)) {
                    this.props.onLayerLoading(event.layer.layerId);
                }
                event.layer.on('loading', (loadingEvent) => {
                    hadError = false;
                    this.props.onLayerLoading(loadingEvent.target.layerId);
                });
                event.layer.on('load', (loadEvent) => { this.props.onLayerLoad(loadEvent.target.layerId, hadError); });
                event.layer.on('tileerror', (errorEvent) => {
                    const isError = errorEvent.target.onError ? (errorEvent.target.onError(errorEvent)) : true;
                    if (isError) {
                        hadError = true;
                        this.props.onLayerError(errorEvent.target.layerId);
                    }
                });
            }
        });

        this.drawControl = null;

        if (this.props.registerHooks) {
            this.registerHooks();
        }
    },
    componentWillReceiveProps(newProps) {

        if (newProps.mousePointer !== this.props.mousePointer) {
            this.setMousePointer(newProps.mousePointer);
        }
        // update the position if the map is not the source of the state change
        if (this.map && newProps.mapStateSource !== this.props.id) {
            this._updateMapPositionFromNewProps(newProps);
        }
        if (newProps.zoomControl !== this.props.zoomControl) {
            if (newProps.zoomControl) {
                this.map.addControl(L.control.zoom());
            } else {
                this.map.removeControl(this.map.zoomControl);
            }
        }
        if (this.map && newProps.resize !== this.props.resize) {
            setTimeout(() => {
                this.map.invalidateSize(false);
            }, 0);
        }
        return false;
    },
    componentWillUnmount() {
        this.map.remove();
    },
    getResolutions() {
        return this.props.resolutions;
    },
    render() {
        const map = this.map;
        const mapProj = this.props.projection;
        const children = map ? React.Children.map(this.props.children, child => {
            return child ? React.cloneElement(child, {
                map: map,
                projection: mapProj,
                zoomOffset: this.zoomOffset,
                onInvalid: this.props.onInvalidLayer,
                onClick: this.props.onClick
            }) : null;
        }) : null;
        return (
            <div id={this.props.id} style={this.props.style}>
                {children}
            </div>
        );
    },
    _updateMapPositionFromNewProps(newProps) {
        // current implementation will update the map only if the movement
        // between 12 decimals in the reference system to avoid rounded value
        // changes due to float mathematic operations.
        const isNearlyEqual = function(a, b) {
            if (a === undefined || b === undefined) {
                return false;
            }
            return ( a.toFixed(12) - (b.toFixed(12))) === 0;
        };

        // getting all centers we need to check
        const newCenter = newProps.center;
        const currentCenter = this.props.center;
        const mapCenter = this.map.getCenter();
        // checking if the current props are the same
        const propsCentersEqual = isNearlyEqual(newCenter.x, currentCenter.x) &&
                                  isNearlyEqual(newCenter.y, currentCenter.y);
        // if props are the same nothing to do, otherwise
        // we need to check if the new center is equal to map center
        const centerIsNotUpdated = propsCentersEqual ||
                                   (isNearlyEqual(newCenter.x, mapCenter.lng) &&
                                    isNearlyEqual(newCenter.y, mapCenter.lat));

        // getting all zoom values we need to check
        const newZoom = newProps.zoom;
        const currentZoom = this.props.zoom;
        const mapZoom = this.map.getZoom();
        // checking if the current props are the same
        const propsZoomEqual = newZoom === currentZoom;
        // if props are the same nothing to do, otherwise
        // we need to check if the new zoom is equal to map zoom
        const zoomIsNotUpdated = propsZoomEqual || newZoom === mapZoom;

         // do the change at the same time, to avoid glitches
        if (!centerIsNotUpdated && !zoomIsNotUpdated) {
            this.map.setView([newProps.center.y, newProps.center.x], Math.round(newProps.zoom));
        } else if (!zoomIsNotUpdated) {
            this.map.setZoom(newProps.zoom);
        } else if (!centerIsNotUpdated) {
            this.map.setView([newProps.center.y, newProps.center.x]);
        }
    },
    updateMapInfoState() {
        const bbox = this.map.getBounds().toBBoxString().split(',');
        const size = {
            height: this.map.getSize().y,
            width: this.map.getSize().x
        };
        var center = this.map.getCenter();
        this.props.onMapViewChanges({x: center.lng, y: center.lat, crs: "EPSG:4326"}, this.map.getZoom(), {
            bounds: {
                minx: bbox[0],
                miny: bbox[1],
                maxx: bbox[2],
                maxy: bbox[3]
            },
            crs: 'EPSG:4326',
            rotation: 0
        }, size, this.props.id, this.props.projection );
    },
    setMousePointer(pointer) {
        if (this.map) {
            const mapDiv = this.map.getContainer();
            mapDiv.style.cursor = pointer || 'auto';
        }
    },
    mouseMoveEvent(event) {
        let pos = event.latlng.wrap();
        this.props.onMouseMove({
            x: pos.lng || 0.0,
            y: pos.lat || 0.0,
            crs: "EPSG:4326",
            pixel: {
                x: event.containerPoint.x,
                y: event.containerPoint.x
            }
        });
    },
    registerHooks() {
        mapUtils.registerHook(mapUtils.EXTENT_TO_ZOOM_HOOK, (extent) => {
            var repojectedPointA = CoordinatesUtils.reproject([extent[0], extent[1]], this.props.projection, 'EPSG:4326');
            var repojectedPointB = CoordinatesUtils.reproject([extent[2], extent[3]], this.props.projection, 'EPSG:4326');
            return this.map.getBoundsZoom([[repojectedPointA.y, repojectedPointA.x], [repojectedPointB.y, repojectedPointB.x]]) - 1;
        });
        mapUtils.registerHook(mapUtils.RESOLUTIONS_HOOK, () => {
            return this.getResolutions();
        });
        mapUtils.registerHook(mapUtils.COMPUTE_BBOX_HOOK, (center, zoom) => {
            let latLngCenter = L.latLng([center.y, center.x]);
            // this call will use map internal size
            let topLeftPoint = this.map._getNewTopLeftPoint(latLngCenter, zoom);
            let pixelBounds = new L.Bounds(topLeftPoint, topLeftPoint.add(this.map.getSize()));
            let southWest = this.map.unproject(pixelBounds.getBottomLeft(), zoom);
            let northEast = this.map.unproject(pixelBounds.getTopRight(), zoom);
            let bbox = new L.LatLngBounds(southWest, northEast).toBBoxString().split(',');
            return {
                bounds: {
                    minx: bbox[0],
                    miny: bbox[1],
                    maxx: bbox[2],
                    maxy: bbox[3]
                },
                crs: 'EPSG:4326',
                rotation: 0
            };
        });
        mapUtils.registerHook(mapUtils.GET_PIXEL_FROM_COORDINATES_HOOK, (pos) => {
            let latLng = CoordinatesUtils.reproject(pos, this.props.projection, 'EPSG:4326');
            let pixel = this.map.latLngToContainerPoint([latLng.x, latLng.y]);
            return [pixel.x, pixel.y];
        });
        mapUtils.registerHook(mapUtils.GET_COORDINATES_FROM_PIXEL_HOOK, (pixel) => {
            let pos = CoordinatesUtils.reproject(this.map.containerPointToLatLng(pixel), 'EPSG:4326', this.props.projection);
            return [pos.x, pos.y];
        });
    }
});

module.exports = LeafletMap;
