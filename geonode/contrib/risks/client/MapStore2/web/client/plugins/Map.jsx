/*
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {connect} = require('react-redux');
const {createSelector} = require('reselect');

const Spinner = require('react-spinkit');
require('./map/css/map.css');

const Message = require('../components/I18N/Message');
const {isString} = require('lodash');
let plugins;
/**
 * The Map plugin allows adding mapping library dependent functionality using support tools.
 * Some are already available for the supported mapping libraries (openlayers, leaflet, cesium), but it's possible to develop new ones.
 * An example is the MeasurementSupport tool that allows implementing measurement on a map.
 * The list of enabled tools can be configured using the tools property, as in the following example:
 *
 * ```
 * {
 * "name": "Map",
 * "cfg": {
 *     "tools": ["measurement", "locate", "overview", "scalebar", "draw", "highlight"]
 *   ...
 *  }
 * }
 * ```
 * // Each tool can be configured using the toolsOptions. Tool configuration can be mapping library dependent:
 * ```
 * "toolsOptions": {
 *        "scalebar": {
 *            "leaflet": {
 *                "position": "bottomright"
 *            }
 *            ...
 *        }
 *        ...
 *    }
 *
 * ```
 * or not
 * ```
 * "toolsOptions": {
 * "scalebar": {
 *        "position": "bottomright"
 *        ...
 *    }
 *    ...
 * ```
 * }
 * In addition to standard tools, you can also develop your own, ad configure them to be used.
 *
 * To do that you need to:
 *  - develop a tool Component, in JSX (e.g. TestSupport), for each supported mapping library
 * ```
 * const React = require('react');
 *    const TestSupport = React.createClass({
 *     propTypes: {
 *            label: React.PropTypes.string
 *        },
 *        render() {
 *            alert(this.props.label);
 *            return null;
 *        }
 *    });
 *    module.exports = TestSupport;
 * ```
 *  - include the tool(s) in the requires section of plugins.js amd give it a name:
 * ```
 *    module.exports = {
 *        plugins: {
 *            MapPlugin: require('../plugins/Map'),
 *            ...
 *        },
 *        requires: {
 *            ...
 *            TestSupportLeaflet: require('../components/map/leaflet/TestSupport')
 *        }
 *    };
 * ```
 *  - configure the Map plugin including the new tool and related options. You can configure the tool to be used for each mapping library, giving it a name and impl attributes, where:
 * ```
 *    {
 *      "name": "Map",
 *      "cfg": {
 *        "tools": ["measurement", "locate", "overview", "scalebar", "draw", {
 *          "leaflet": {
 *            "name": "test",
 *            "impl": "{context.TestSupportLeaflet}"
 *          }
 *          }],
 *        "toolsOptions": {
 *          "test": {
 *            "label": "ciao"
 *          }
 *          ...
 *        }
 *      }
 *    }
 * ```
 *  - name is a unique name for the tool
 *  - impl is a placeholder (“{context.ToolName}”) where ToolName is the name you gave the tool in plugins.js (TestSupportLeaflet in our example)
 * @memberof plugins
 * @class Map
 * @static
 *
 */
const MapPlugin = React.createClass({
    propTypes: {
        mapType: React.PropTypes.string,
        map: React.PropTypes.object,
        layers: React.PropTypes.array,
        zoomControl: React.PropTypes.bool,
        mapLoadingMessage: React.PropTypes.string,
        loadingSpinner: React.PropTypes.bool,
        loadingError: React.PropTypes.string,
        tools: React.PropTypes.array,
        options: React.PropTypes.object,
        toolsOptions: React.PropTypes.object,
        actions: React.PropTypes.object,
        features: React.PropTypes.array
    },
    getDefaultProps() {
        return {
            mapType: 'leaflet',
            actions: {},
            zoomControl: false,
            mapLoadingMessage: "map.loading",
            loadingSpinner: true,
            tools: ["measurement", "locate", "overview", "scalebar", "draw", "highlight"],
            options: {},
            toolsOptions: {
                measurement: {},
                locate: {},
                scalebar: {
                    leaflet: {
                      position: "bottomright"
                    }
                },
                overview: {
                    overviewOpt: {
                        position: 'bottomright',
                        collapsedWidth: 25,
                        collapsedHeight: 25,
                        zoomLevelOffset: -5,
                        toggleDisplay: true
                    },
                    layers: [{type: "osm"}]
                }
            }
        };
    },
    componentWillMount() {
        this.updatePlugins(this.props);
    },
    componentWillReceiveProps(newProps) {
        if (newProps.mapType !== this.props.mapType || newProps.actions !== this.props.actions) {
            this.updatePlugins(newProps);
        }
    },
    getHighlightLayer(projection, index) {
        return (<plugins.Layer type="vector" srs={projection} position={index} key="highlight" options={{name: "highlight"}}>
                    {this.props.features.map( (feature) => {
                        return (<plugins.Feature
                            key={feature.id}
                            type={feature.type}
                            geometry={feature.geometry}/>);
                    })}
                </plugins.Layer>);
    },
    getTool(tool) {
        if (isString(tool)) {
            return {
                name: tool,
                impl: plugins.tools[tool]
            };
        }
        return tool[this.props.mapType] || tool;
    },
    renderLayers() {
        const projection = this.props.map.projection || 'EPSG:3857';
        return this.props.layers.map((layer, index) => {
            return (
                <plugins.Layer type={layer.type} srs={projection} position={index} key={layer.id || layer.name} options={layer}>
                    {this.renderLayerContent(layer)}
                </plugins.Layer>
            );
        }).concat(this.props.features && this.props.features.length && this.getHighlightLayer(projection, this.props.layers.length) || []);
    },
    renderLayerContent(layer) {
        if (layer.features && layer.type === "vector") {
            return layer.features.map( (feature) => {
                return (
                    <plugins.Feature
                        key={feature.id}
                        type={feature.type}
                        geometry={feature.geometry}
                        msId={feature.id}
                        featuresCrs={ layer.featuresCrs || 'EPSG:4326' }
                        // FEATURE STYLE OVERWRITE LAYER STYLE
                        style={ feature.style || layer.style || null }
                        properties={feature.properties}/>
                );
            });
        }
        return null;
    },

    renderSupportTools() {
        return this.props.tools.map((tool) => {
            const Tool = this.getTool(tool);
            const options = (this.props.toolsOptions[Tool.name] && this.props.toolsOptions[Tool.name][this.props.mapType]) || this.props.toolsOptions[Tool.name] || {};
            return <Tool.impl key={Tool.name} {...options}/>;
        });
    },
    render() {
        if (this.props.map) {
            return (
                <plugins.Map id="map"
                    {...this.props.options}
                    {...this.props.map}
                    zoomControl={this.props.zoomControl}>
                    {this.renderLayers()}
                    {this.renderSupportTools()}
                </plugins.Map>
            );
        }
        if (this.props.loadingError) {
            return (<div style={{
                width: "100%",
                height: "100%",
                display: "flex",
                justifyContent: "center",
                alignItems: "center"
            }} className="mapErrorMessage">
                <Message msgId="map.loadingerror"/>:
                    {this.props.loadingError}
            </div>);
        }
        return (<div style={{
            width: "100%",
            height: "100%",
            display: "flex",
            justifyContent: "center",
            alignItems: "center"
            }} className="mapLoadingMessage">
                {this.props.loadingSpinner ? <Spinner spinnerName="circle" overrideSpinnerClassName="spinner"/> : null}
                <Message msgId={this.props.mapLoadingMessage}/>
        </div>);
    },
    updatePlugins(props) {
        plugins = require('./map/index')(props.mapType, props.actions);
    }
});
const {mapSelector} = require('../selectors/map');
const {layerSelectorWithMarkers} = require('../selectors/layers');

const highlightSelector = (state) => state.highlight && state.highlight.select;

const selector = createSelector(
    [
        mapSelector,
        layerSelectorWithMarkers,
        highlightSelector,
        (state) => state.mapInitialConfig && state.mapInitialConfig.loadingError && state.mapInitialConfig.loadingError.data
    ], (map, layers, features, loadingError) => ({
        map,
        layers,
        features,
        loadingError
    })
);
module.exports = {
    MapPlugin: connect(selector)(MapPlugin),
    reducers: { draw: require('../reducers/draw') }
};
