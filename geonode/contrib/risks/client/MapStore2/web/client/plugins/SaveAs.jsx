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
// const {toggleControl} = require('../actions/controls');
const {loadMapInfo} = require('../actions/config');
const MetadataModal = require('../components/maps/modals/MetadataModal');
const {createMap, createThumbnail, onDisplayMetadataEdit} = require('../actions/maps');
const {editMap, updateCurrentMap, errorCurrentMap, resetCurrentMap} = require('../actions/currentMap');
const {mapSelector} = require('../selectors/map');
const stateSelector = state => state;
const {layersSelector} = require('../selectors/layers');
const {indexOf} = require('lodash');

const LayersUtils = require('../utils/LayersUtils');

const selector = createSelector(mapSelector, stateSelector, layersSelector, (map, state, layers) => ({
    currentZoomLvl: map && map.zoom,
    show: state.controls && state.controls.saveAs && state.controls.saveAs.enabled,
    mapType: (state && ((state.home && state.home.mapType) || (state.maps && state.maps.mapType))) || "leaflet",
    newMapId: state.currentMap && state.currentMap.newMapId,
    map,
    user: state.security && state.security.user,
    currentMap: state.currentMap,
    layers
}));

const SaveAs = React.createClass({
    propTypes: {
        show: React.PropTypes.bool,
        newMapId: React.PropTypes.number,
        map: React.PropTypes.object,
        user: React.PropTypes.object,
        mapType: React.PropTypes.string,
        layers: React.PropTypes.array,
        params: React.PropTypes.object,
        currentMap: React.PropTypes.object,
        // CALLBACKS
        onClose: React.PropTypes.func,
        onCreateThumbnail: React.PropTypes.func,
        onUpdateCurrentMap: React.PropTypes.func,
        onErrorCurrentMap: React.PropTypes.func,
        onSave: React.PropTypes.func,
        editMap: React.PropTypes.func,
        resetCurrentMap: React.PropTypes.func,
        onMapSave: React.PropTypes.func,
        loadMapInfo: React.PropTypes.func
    },
    contextTypes: {
        router: React.PropTypes.object
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
        if (map && props.currentMap.mapId && !this.props.newMapId) {
            this.context.router.push("/viewer/" + props.mapType + "/" + props.currentMap.mapId);
            this.props.resetCurrentMap();
        }
    },
    getInitialState() {
        return {
            displayMetadataEdit: false
        };
    },
    render() {
        let map = (this.state && this.state.loading) ? assign({updating: true}, this.props.currentMap) : this.props.currentMap;
        return (
            <MetadataModal ref="metadataModal"
                displayPermissionEditor={false}
                show={this.props.currentMap.displayMetadataEdit}
                onEdit={this.props.editMap}
                onUpdateCurrentMap={this.props.onUpdateCurrentMap}
                onErrorCurrentMap={this.props.onErrorCurrentMap}
                onHide={this.close}
                onClose={this.close}
                map={map}
                onSave={this.saveMap}
            />
        );
    },
    close() {
        this.props.onUpdateCurrentMap([], this.props.map && this.props.map.thumbnail);
        this.props.onErrorCurrentMap([], this.props.map && this.props.map.id);
        this.props.onClose();
    },
    // this method creates the content for the Map Resource
    createV2Map() {
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
        return resultingmap;
    },
    saveMap(id, name, description) {
        this.props.editMap(this.props.map);
        let thumbComponent = this.refs.metadataModal.refs.thumbnail;
        let attributes = {"owner": this.props.user && this.props.user.name || null};
        let metadata = {
            name,
            description,
            attributes
        };
        thumbComponent.getThumbnailDataUri( (data) => {
            this.props.onMapSave(metadata, JSON.stringify(this.createV2Map()), {
                data,
                category: "THUMBNAIL",
                name: thumbComponent.generateUUID()
            });
        });
    }
});


module.exports = {
    SaveAsPlugin: connect(selector,
    {
        onClose: () => onDisplayMetadataEdit(false),
        onUpdateCurrentMap: updateCurrentMap,
        onErrorCurrentMap: errorCurrentMap,
        onMapSave: createMap,
        loadMapInfo,
        editMap,
        resetCurrentMap,
        onDisplayMetadataEdit,
        onCreateThumbnail: createThumbnail
    })(assign(SaveAs, {
        BurgerMenu: {
            name: 'saveAs',
            position: 900,
            text: <Message msgId="saveAs"/>,
            icon: <Glyphicon glyph="floppy-open"/>,
            action: editMap.bind(null, {}),
            selector: (state) => {
                if (state && state.controls && state.controls.saveAs && state.controls.saveAs.allowedRoles) {
                    return indexOf(state.controls.saveAs.allowedRoles, state && state.security && state.security.user && state.security.user.role) !== -1 ? {} : { style: {display: "none"} };
                }
                return state && state.security && state.security.user ? {} : { style: {display: "none"} };
            }
        }
    }))
};
