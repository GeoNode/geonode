/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');

var DebugUtils = require('../../utils/DebugUtils');
const LayersUtils = require('../../utils/LayersUtils');

var {connect} = require('react-redux');
var {bindActionCreators, combineReducers} = require('redux');

var {Provider} = require('react-redux');

var {changeBrowserProperties} = require('../../actions/browser');

var ConfigUtils = require('../../utils/ConfigUtils');

var Debug = require('../../components/development/Debug');
var mapConfig = require('../../reducers/map');
var layers = require('../../reducers/layers');
var browser = require('../../reducers/browser');
var layertree = require('./reducers/layertree');

var LMap = require('../../components/map/leaflet/Map');
var LLayer = require('../../components/map/leaflet/Layer');

var {changeMapView, changeZoomLevel} = require('../../actions/map');
var {toggleNode, removeNode, changeLayerProperties,
     changeGroupProperties, updateNode, sortNode} = require('../../actions/layers');
var {showSettings, hideSettings, updateOpacity} = require('./actions/layertree');
var assign = require('object-assign');
var TOC = require('../../components/TOC/TOC');
var Group = require('./components/Group');
var LayerOrGroup = require('./components/LayerOrGroup');
var {Panel, Modal, Label, Button} = require('react-bootstrap');

let {sources, layers: mapLayers} = require('./config.json');

var Slider = require('react-nouislider');

ConfigUtils.setupSources(sources, "gxp_wmssource");
ConfigUtils.setupLayers(mapLayers, sources, ["gxp_osmsource", "gxp_wmssource", "gxp_googlesource", "gxp_bingsource", "gxp_mapquestsource"]);
mapLayers = mapLayers.map(ConfigUtils.setLayerId);

const getGroup = (group, allLayers) => {
    let groupName = group || 'Default';
    let subGroups = allLayers.filter((layer) => layer.group.indexOf(groupName + '.') === 0)
        .map((layer) => layer.group).reduce((previous, subGroupName) => {
            let name = subGroupName.substring(subGroupName.indexOf('.') + 1);
            return previous.indexOf(name) === -1 ? previous.concat([name]) : previous;
        }, []);

    return assign({}, {
        id: groupName,
        name: groupName,
        title: groupName,
        nodes: allLayers.filter((layer) => layer.group === group).map((layer) => layer.id).concat(
            subGroups.map((subGroupName) => {
                return {
                    id: groupName + '.' + subGroupName,
                    type: "group",
                    name: groupName + '.' + subGroupName,
                    title: subGroupName,
                    expanded: true,
                    nodes: allLayers.filter((layer) => layer.group === (groupName + '.' + subGroupName)).map((layer) => layer.id)
                };
            })
        ),
        expanded: true
    });
};

const getLayersByGroup = function(configLayers) {
    let i = 0;
    let lyrs = configLayers.map((layer) => assign({}, layer, {storeIndex: i++}));
    let groupNames = lyrs.reduce((groups, layer) => {
        let groupName = layer.group;
        if (groupName.indexOf('.') !== -1) {
            groupName = groupName.split('.')[0];
        }
        return groups.indexOf(groupName) === -1 ? groups.concat([groupName]) : groups;
    }, []);
    return groupNames.map((group) => getGroup(group, lyrs));
};

let groupsTree = getLayersByGroup(mapLayers);

// Here we create the store, we use Debug utils but is not necessary
// Insteed we need to pass here map configuration
let store = DebugUtils.createDebugStore(combineReducers({browser, mapConfig, layers, layertree}),
        {mapConfig: {
            zoom: 14,
            center: {
                y: 43.776652415109766,
                x: 11.256354990831623,
                crs: "EPSG:4326"
            },
            projection: "EPSG:900913"
        },
        layers: {
            flat: mapLayers,
            groups: groupsTree
        },
        browser: {}});

require('../../components/map/leaflet/plugins/WMSLayer');
require('../../components/map/leaflet/plugins/OSMLayer');
require('../../components/map/leaflet/plugins/BingLayer');
require('../../components/map/leaflet/plugins/GoogleLayer');
require('../../components/map/leaflet/plugins/VectorLayer');

    /**
    * Detect Browser's properties and save in app state.
    **/
store.dispatch(changeBrowserProperties(ConfigUtils.getBrowserProperties()));

let MyMap = React.createClass({
    propTypes: {
        mapConfig: ConfigUtils.PropTypes.config,
        layers: React.PropTypes.object,
        groups: React.PropTypes.array,
        changeMapView: React.PropTypes.func,
        changeZoomLevel: React.PropTypes.func,
        toggleNode: React.PropTypes.func,
        showSettings: React.PropTypes.func,
        hideSettings: React.PropTypes.func,
        updateOpacity: React.PropTypes.func,
        updateNode: React.PropTypes.func,
        removeNode: React.PropTypes.func,
        sortNode: React.PropTypes.func,
        changeLayerProperties: React.PropTypes.func,
        changeGroupProperties: React.PropTypes.func,
        browser: React.PropTypes.object,
        controls: React.PropTypes.object,
        zoom: React.PropTypes.number
    },
    getDefaultProps() {
        return {};
    },
    renderLayers() {
        return this.props.layers.flat.map(function(layer, index) {
            var options = assign({}, layer, {srs: "EPSG:3857"});
            return <LLayer type={layer.type} position={index} key={layer.id + ":::" + index} options={options} />;
        });
    },
    render() {
        return (<div id="viewer" >
                <LMap key="map"
                    center={this.props.mapConfig.center}
                    zoom={this.props.mapConfig.zoom}
                    projection={this.props.mapConfig.projection}
                    onMapViewChanges={this.manageNewMapView}
                >
                    {this.renderLayers()}
                </LMap>

                <Panel style={{position: "fixed", top: "50px", right: "50px", width: "400px", bottom: "50px", overflow: "auto"}}>
                    <TOC onSort={this.props.sortNode} nodes={this.props.layers.groups}>
                        <Group propertiesChangeHandler={this.props.changeGroupProperties}
                            onRemove={(node) => this.props.removeNode(node.id, 'groups')}
                            onToggle={(group, status) => this.props.toggleNode(group, 'groups', status)}
                            onSort={this.props.sortNode}
                            >
                            <LayerOrGroup
                                onLegend={(node) => this.props.toggleNode(node.id, 'layers', node.expanded)}
                                onSettings={(node, nodeType, options) => this.props.showSettings(node.id, nodeType, options)}
                                propertiesChangeHandler={this.props.changeLayerProperties}
                                groupPropertiesChangeHandler={this.props.changeGroupProperties}
                                onRemoveGroup={(node) => this.props.removeNode(node.id, 'groups')}
                                onSortGroup={this.props.sortNode}
                            />
                        </Group>
                    </TOC>
                </Panel>
                <Modal.Dialog style={{visibility: this.props.controls.Settings.expanded ? "visible" : "hidden"}}>
                    <Modal.Header><Modal.Title>Opacity</Modal.Title></Modal.Header>
                    <Modal.Body>
                        <Slider
                            start={[Math.round(this.props.controls.Settings.options.opacity * 100)]}
                            range={{min: 0, max: 100}}
                            onChange={this.props.updateOpacity}
                        />
                    <Label>{Math.round(this.props.controls.Settings.options.opacity * 100) + "%"}</Label>
                    </Modal.Body>
                    <Modal.Footer>
                        <Button onClick={this.props.hideSettings}>Close</Button>
                        <Button bsStyle="primary" onClick={() => {
                            this.props.updateNode(
                                this.props.controls.Settings.node,
                                this.props.controls.Settings.nodeType,
                                this.props.controls.Settings.options
                            );
                            this.props.hideSettings();
                        }}>Save changes</Button>
                    </Modal.Footer>
                </Modal.Dialog>
          </div>
           );
    },
    manageNewMapView(center, zoom, bbox, size, mapStateSource, projection) {
        this.props.changeMapView(center, zoom, bbox, size, mapStateSource, projection);
    }
});
let App = connect((state) => {
    return {
        mapConfig: state.mapConfig,
        browser: state.browser,
        layers: state.layers ? LayersUtils.denormalizeGroups(state.layers.flat, state.layers.groups) : state.layers,
        controls: state.layertree
    };
}, dispatch => {
    return bindActionCreators({
        changeMapView,
        changeZoomLevel,
        toggleNode,
        removeNode,
        sortNode,
        changeLayerProperties,
        changeGroupProperties,
        showSettings,
        hideSettings,
        updateOpacity,
        updateNode
    }, dispatch);
})(MyMap);

ReactDOM.render(
        <Provider store={store}>
            <div>
                <App />
                <Debug/>
            </div>
        </Provider>,
        document.getElementById('container')
    );
