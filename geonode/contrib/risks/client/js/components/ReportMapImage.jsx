/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {connect} = require('react-redux');
const mapType = "leaflet";
const SnapshotSupport = require('../../MapStore2/web/client/components/mapcontrols/Snapshot/SnapshotSupport')(mapType);
const {reportMapReady, generateMapError} = require('../actions/report');


const ReportMap = React.createClass({
    propTypes: {
            map: React.PropTypes.object,
            layers: React.PropTypes.array,
            style: React.PropTypes.object,
            activeSections: React.PropTypes.object,
            authParam: React.PropTypes.object,
            imageReady: React.PropTypes.func,
            onSnapshotError: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            map: null,
            layers: [],
            style: {height: "400px", width: "400px", display: "block", border: "1px solid black"}
        };
    },
    renderGrabMaps() {
        const map = this.props.map || {};
        const mapconf = {
            "config": {
                  "projection": map.projection ? map.projection : "EPSG:3857",
                  "units": map.units ? map.units : "m",
                  "center": map.center,
                  "zoom": map.zoom,
                  "mapId": false,
                  "size": {
                    "width": 420,
                    "height": 400
                  },
                  "mapStateSource": "map"
              },
            "layers": this.props.layers,
            "allowTaint": false
        };
        return (
            <div
                key="hiddenGrabMaps"
                style={{zIndex: -9999}}>
                <SnapshotSupport.GrabMap
                    active={true}
                    snapstate={{state: "SHOOTING"}}
                    timeout={0}
                    onSnapshotReady={this.imageReady}
                    onSnapshotError={this.props.onSnapshotError}
                {...mapconf}/>
            </div>);
    },
    render() {
        return this.renderGrabMaps();
    },
    imageReady(canvas) {
        try {
            const dataURL = canvas.toDataURL("image/png");
            this.props.imageReady(dataURL);

        }catch(e) {
            this.props.onSnapshotError(e);
        }
    }
});

module.exports = connect((state) => {
    return {
        map: state.map && state.map.present || state.mapInitialConfig || {},
        layers: state.layers && state.layers.flat || []
    };
}, {
    imageReady: reportMapReady,
    onSnapshotError: generateMapError
})(ReportMap);
