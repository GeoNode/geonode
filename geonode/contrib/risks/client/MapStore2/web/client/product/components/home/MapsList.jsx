/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');

var I18N = require('../../../components/I18N/I18N');
var {Label, FormControl, FormGroup} = require('react-bootstrap');
const {connect} = require('react-redux');
const {updateMapMetadata, deleteMap, createThumbnail} = require('../../../actions/maps');
const MapGrid = connect(() => ({}), {updateMapMetadata, deleteMap, createThumbnail})(require('../../../components/maps/MapGrid'));

var MapsList = React.createClass({
    propTypes: {
        maps: React.PropTypes.object,
        mapType: React.PropTypes.string,
        title: React.PropTypes.string,
        onChangeMapType: React.PropTypes.func,
        onGoToMap: React.PropTypes.func
    },
    render() {
        if (this.props.maps) {
            return (
                <div>
                <Label><I18N.Message msgId="manager.mapTypes_combo"/></Label>
                <FormGroup bsSize="small">
                    <FormControl value={this.props.mapType} componentClass="select" ref="mapType" onChange={this.props.onChangeMapType}>
                        <option value="leaflet" key="leaflet">Leaflet</option>
                        <option value="openlayers" key="openlayer">OpenLayers</option>
                    </FormControl>
                </FormGroup>
                <h3>{this.props.title}</h3>
                <MapGrid mapType={this.props.mapType}
                    viewerUrl={this.props.onGoToMap}
                    loading={this.props.maps && this.props.maps.loading}
                    maps={this.props.maps && this.props.maps.results ? this.props.maps.results : []}
                    panelProps={{className: "mapmanager",
                        collapsible: true,
                        defaultExpanded: true}}
                    />
             </div>
         );
        }
        return null;
    }
});

module.exports = MapsList;
