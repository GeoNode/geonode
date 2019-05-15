/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const assign = require('object-assign');

const ScaleBox = require("../mapcontrols/scale/ScaleBox");
const {Button, Glyphicon} = require('react-bootstrap');

let PMap;
let Layer;
let Feature;

const MapPreview = React.createClass({
    propTypes: {
        map: React.PropTypes.object,
        layers: React.PropTypes.array,
        style: React.PropTypes.object,
        scales: React.PropTypes.array,
        onChangeZoomLevel: React.PropTypes.func,
        onMapViewChanges: React.PropTypes.func,
        onMapRefresh: React.PropTypes.func,
        height: React.PropTypes.number,
        width: React.PropTypes.number,
        mapType: React.PropTypes.string,
        enableRefresh: React.PropTypes.bool,
        enableScalebox: React.PropTypes.bool,
        resolutions: React.PropTypes.array,
        printRatio: React.PropTypes.number,
        layout: React.PropTypes.string,
        layoutSize: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            map: null,
            layers: [],
            mapType: "leaflet",
            style: {display: "block", border: "1px solid black", position: "relative"},
            onChangeZoomLevel: () => {},
            onMapViewChanges: () => {},
            onMapRefresh: () => {},
            width: 370,
            height: 270,
            enableRefresh: true,
            enableScalebox: true,
            printRatio: 96.0 / 72.0
        };
    },
    componentWillMount() {
        PMap = require('../map/' + this.props.mapType + '/Map');
        Layer = require('../map/' + this.props.mapType + '/Layer');
        require('../map/' + this.props.mapType + '/plugins/index');
        Feature = require('../map/' + this.props.mapType + '/index').Feature;
    },
    getRatio() {
        if (this.props.width && this.props.layoutSize && this.props.resolutions) {
            return this.props.layoutSize.width / this.props.width * this.props.printRatio;
        }
        return 1;
    },
    getResolutions() {
        if (this.props.width && this.props.layoutSize && this.props.resolutions) {
            return this.props.resolutions.map((resolution) => resolution * this.getRatio());
        }
        return this.props.resolutions;
    },
    adjustResolution(layer) {
        const ratio = this.getRatio();
        const dpi = Math.round((96.0 / ratio));
        return assign({}, layer, {
            params: assign({}, layer.params, {
                "format_options": "dpi:" + dpi,
                "MAP.RESOLUTION": dpi
            })
        });
    },
    renderLayerContent(layer) {
        if (layer.features && layer.type === "vector") {
            return layer.features.map( (feature) => {
                return (
                    <Feature
                        key={feature.id}
                        type={feature.type}
                        geometry={feature.geometry}
                        msId={feature.id}
                        featuresCrs={ layer.featuresCrs || 'EPSG:4326' }
                        style={ feature.style || layer.style || null }/>
                );
            });
        }
        return null;
    },
    render() {
        const style = assign({}, this.props.style, {
            width: this.props.width + "px",
            height: this.props.height + "px"
        });
        const resolutions = this.getResolutions();
        const mapOptions = resolutions ? {view: {resolutions}} : {};
        const projection = this.props.map.projection || 'EPSG:3857';
        return this.props.map && this.props.map.center ?
        (
                <div className="print-map-preview"><PMap
                ref="mappa"
                {...this.props.map}
                resize={this.props.height}
                style={style}
                interactive={false}
                onMapViewChanges={this.props.onMapViewChanges}
                zoomControl={false}
                zoom={this.props.map.zoom}
                center={this.props.map.center}
                id="print_preview"
                registerHooks={false}
                mapOptions={mapOptions}
                >
                {this.props.layers.map((layer, index) =>
                    <Layer key={layer.id || layer.name} position={index} type={layer.type}
                        options={assign({}, this.adjustResolution(layer), {srs: projection})}>
                        {this.renderLayerContent(layer)}
                    </Layer>

                )}
                </PMap>
                {this.props.enableScalebox ? <ScaleBox id="mappreview-scalebox"
                    currentZoomLvl={this.props.map.scaleZoom}
                    scales={this.props.scales}
                    onChange={this.props.onChangeZoomLevel}
                    /> : null}
                {this.props.enableRefresh ? <Button bsStyle="primary" onClick={this.props.onMapRefresh} className="print-mappreview-refresh"><Glyphicon glyph="refresh"/></Button> : null}
                </div>
        ) : <span/>;
    }
});

module.exports = MapPreview;
