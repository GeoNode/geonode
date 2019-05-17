/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var {LMap,
    LLayer,
    Feature
} = require('../index');
const assign = require('object-assign');
const ConfigUtils = require('../../../../utils/ConfigUtils');
require("./snapshotMapStyle.css");
/**
 * GrabMap for OpenLayers map generate a fake-map, hidden, and waits for the
 * layer loading end to generate the snapshot from the canvas.
 * In order to avoid cross origin issues, the allowTaint property have to be set
 * to false if you are not sure that the items come from the same orgin.
 */
let GrabOlMap = React.createClass({
    propTypes: {
            id: React.PropTypes.node,
            config: ConfigUtils.PropTypes.config,
            layers: React.PropTypes.array,
            snapstate: React.PropTypes.object,
            active: React.PropTypes.bool,
            onSnapshotReady: React.PropTypes.func,
            onStatusChange: React.PropTypes.func,
            onSnapshotError: React.PropTypes.func,
            allowTaint: React.PropTypes.bool
    },
    getDefaultProps() {
        return {
            config: null,
            layers: [],
            snapstate: {state: "DISABLED"},
            active: false,
            onSnapshotReady: () => {},
            onStatusChange: () => {},
            onSnapshotError: () => {}
        };
    },
    renderLayers(layers) {
        if (layers) {
            let projection = this.props.config.projection || 'EPSG:3857';
            let me = this; // TODO find the reason why the arrow function doesn't get this object
            return layers.map((layer, index) => {
                var options = assign({}, layer, {srs: projection}, (layer.type === "wms") ? {forceProxy: !this.props.allowTaint} : {});
                return (<LLayer type={layer.type} position={index} key={layer.id || layer.name} options={options}>
                    {me.renderLayerContent(layer)}
                </LLayer>);
            });
        }
        return null;
    },
    renderLayerContent(layer) {
        if (layer.features && layer.type === "vector") {
            // TODO remove this DIV. What container can be used for this component.
            return layer.features.map( (feature) => {
                return (<Feature
                    key={feature.id}
                    type={feature.type}
                    geometry={feature.geometry}/>);
            });
        }
        return null;
    },
    shouldComponentUpdate(nextProps) {
        return nextProps.active || (nextProps.active !== this.props.active);
    },
    componentDidUpdate() {
        if (!this.props.active) {
            this.props.onStatusChange("DISABLED");
            if (this.props.snapstate.error) {
                this.props.onSnapshotError(null);
            }
        }
    },
    render() {
        return (this.props.active) ? (
            <LMap id={"snapshot_hidden_map-" + this.props.id}
                className="snapshot_hidden_map"
                style={{
                    width: this.props.config && this.props.config.size ? this.props.config.size.width : "100%",
                    height: this.props.config && this.props.config.size ? this.props.config.size.height : "100%"
                }}
                center={this.props.config.center}
                zoom={this.props.config.zoom}
                mapStateSource={this.props.config.mapStateSource}
                projection={this.props.config.projection || 'EPSG:3857'}
                zoomControl={false}
                onLayerLoading={this.layerLoading}
                onLayerLoad={this.layerLoad}
                ref={"snapMap"}
            >
                {this.renderLayers(this.props.layers)}
            </LMap>
        ) : null;
    },
    layerLoad() {
        this.toLoad--;
        if (this.toLoad === 0) {
            let map = (this.refs.snapMap) ? this.refs.snapMap.map : null;
            if (map) {
                map.once('postrender', (e) => setTimeout( () => {
                    let canvas = e.map && e.map.getTargetElement() && e.map.getTargetElement().getElementsByTagName("canvas")[0];
                    if (canvas) {
                        this.createSnapshot(canvas);
                    }
                }, 500));
                // map.once('postcompose', (e) => setTimeout( () => this.createSnapshot(e.context.canvas), 100));
            }
        }
    },
    layerLoading() {
        if (this.props.snapstate.state !== "SHOTING") {
            this.props.onStatusChange("SHOTING");

        }
        this.toLoad = (this.toLoad) ? this.toLoad : 0;
        this.toLoad++;
    },
    createSnapshot(canvas) {
        this.props.onSnapshotReady(canvas, null, null, null, this.isTainted(canvas));
    },
    /**
     * Check if the canvas is tainted, so if it is allowed to export images
     * from it.
     */
    isTainted(canvas) {
        if (canvas) {
            let ctx = canvas.getContext("2d");
            try {
                // try to generate a small image
                ctx.getImageData(0, 0, 1, 1);
                return false;
            } catch(err) {
                // check the error code for tainted resources
                return (err.code === 18);
            }
        }

    }
});

require('../../../map/openlayers/plugins/index');

module.exports = GrabOlMap;
