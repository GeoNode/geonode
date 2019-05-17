/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {connect} = require('react-redux');
const {createSelector} = require('reselect');
const assign = require('object-assign');
const {Glyphicon} = require('react-bootstrap');
const Message = require('../components/I18N/Message');
const {toggleControl} = require('../actions/controls');
const {loadMapInfo} = require('../actions/config');
const {updateMap} = require('../actions/maps');
const ConfirmModal = require('../components/maps/modals/ConfirmModal');
const ConfigUtils = require('../utils/ConfigUtils');

const {mapSelector} = require('../selectors/map');
const {layersSelector} = require('../selectors/layers');
const stateSelector = state => state;

const LayersUtils = require('../utils/LayersUtils');

const selector = createSelector(mapSelector, stateSelector, layersSelector, (map, state, layers) => ({
    currentZoomLvl: map && map.zoom,
    show: state.controls && state.controls.save && state.controls.save.enabled,
    map,
    mapId: map && map.mapId,
    layers
}));

const Save = React.createClass({
    propTypes: {
        show: React.PropTypes.bool,
        mapId: React.PropTypes.string,
        onClose: React.PropTypes.func,
        onMapSave: React.PropTypes.func,
        loadMapInfo: React.PropTypes.func,
        map: React.PropTypes.object,
        layers: React.PropTypes.array,
        params: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            onMapSave: () => {},
            loadMapInfo: () => {},
            show: false
        };
    },
    componentWillMount() {
        this.onMissingInfo(this.props);
    },
    componentWillReceiveProps(nextProps) {
        this.onMissingInfo(nextProps);
    },
    onMissingInfo(props) {
        let map = props.map;
        if (map && props.mapId && !map.info) {
            this.props.loadMapInfo(ConfigUtils.getConfigProp("geoStoreUrl") + "extjs/resource/" + props.mapId, props.mapId);
        }
    },
    render() {
        return (<ConfirmModal
            confirmText={<Message msgId="save" />}
            cancelText={<Message msgId="cancel" />}
            titleText={<Message msgId="map.saveTitle" />}
            body={<Message msgId="map.saveText" />}
            show={this.props.show}
            onClose={this.props.onClose}
            onConfirm={this.goForTheUpdate}
            />);
    },
    goForTheUpdate() {
        if (this.props.mapId) {
            if (this.props.map && this.props.layers) {
                let map =
                    {
                        center: this.props.map.center,
                        maxExtent: this.props.map.maxExtent,
                        projection: this.props.map.projection,
                        units: this.props.map.units,
                        zoom: this.props.map.zoom
                    };
                let layers = this.props.layers.map((layer) => {
                    return LayersUtils.saveLayer(layer);
                });
                // Groups are ignored, as they already are defined in the layers
                let resultingmap = {
                    version: 2,
                    // layers are defined inside the map object
                    map: assign({}, map, {layers})
                };
                this.props.onMapSave(this.props.mapId, JSON.stringify(resultingmap));
                this.props.onClose();
            }
        }
    }

});

module.exports = {
    SavePlugin: connect(selector,
    {
        onClose: toggleControl.bind(null, 'save', false),
        onMapSave: updateMap,
        loadMapInfo
    })(assign(Save, {
        BurgerMenu: {
            name: 'save',
            position: 900,
            text: <Message msgId="save"/>,
            icon: <Glyphicon glyph="floppy-open"/>,
            action: toggleControl.bind(null, 'save', null),
            // display the BurgerMenu button only if the map can be edited
            selector: (state) => {
                let map = (state.map && state.map.present) || (state.map) || (state.config && state.config.map) || null;
                if (map && map.mapId && state && state.security && state.security.user) {
                    if (state.maps && state.maps.results) {
                        let mapId = map.mapId;
                        let currentMap = state.maps.results.filter(item=> item && ('' + item.id) === mapId);
                        if (currentMap && currentMap.length > 0 && currentMap[0].canEdit) {
                            return { };
                        }
                    }
                    if (map.info && map.info.canEdit) {
                        return { };
                    }
                }
                return { style: {display: "none"} };
            }
        }
    }))
};
