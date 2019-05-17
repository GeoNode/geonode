/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 *
 */

var React = require('react');
var L = require('leaflet');
var assign = require('object-assign');
require('leaflet.locatecontrol')();
require('leaflet.locatecontrol/dist/L.Control.Locate.css');

L.Control.MSLocate = L.Control.Locate.extend({
    setMap: function(map) {
        this._map = map;
        this._layer = this.options.layer;
        this._layer.addTo(map);
        this._event = undefined;

            // extend the follow marker style and circle from the normal style
        let tmp = {};
        L.extend(tmp, this.options.markerStyle, this.options.followMarkerStyle);
        this.options.followMarkerStyle = tmp;
        tmp = {};
        L.extend(tmp, this.options.circleStyle, this.options.followCircleStyle);
        this.options.followCircleStyle = tmp;
        this._resetVariables();
        this.bindEvents(map);
    },
    _setClasses: function(state) {
        this._map.fire('locatestatus', {state: state});
        return state;
    },
    _toggleContainerStyle: function() {
        if (this._following) {
            this._setClasses('following');
        } else if (this._active) {
            this._setClasses('active');
        }
    },
    _cleanClasses: function() {
        return null;
    },
    setStrings: function(newStrings) {
        this.options.strings = assign({}, this.options.strings, newStrings);
    }
});

let Locate = React.createClass({
    propTypes: {
        map: React.PropTypes.object,
        status: React.PropTypes.string,
        messages: React.PropTypes.object,
        changeLocateState: React.PropTypes.func,
        onLocateError: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            id: 'overview',
            status: "DISABLED",
            changeLocateState: () => {},
            onLocateError: () => {}
        };
    },
    componentDidMount() {
        if (this.props.map ) {
            this.locate = new L.Control.MSLocate(this.defaultOpt);
            this.locate.setMap(this.props.map);
            this.props.map.on('locatestatus', this.locateControlState);
            this.locate.options.onLocationError = this.onLocationError;
            this.locate.options.onLocationOutsideMapBounds = this.onLocationError;
        }
        if (this.props.status.enabled) {
            this.locate.start();
        }
    },
    componentWillReceiveProps(newProps) {
        this.fol = false;
        if (newProps.status !== this.props.status) {
            if ( newProps.status === "ENABLED" && !this.locate._active) {
                this.locate.start();
            }else if (newProps.status === "FOLLOWING" && this.locate._active && !this.locate._following) {
                this.fol = true;
                this.locate.stop();
                this.locate.start();
            }else if ( newProps.status === "DISABLED") {
                this.locate._following = false;
                this.locate.stop();
            }
        }
        if (newProps.messages !== this.props.messages) {
            this.locate.setStrings(newProps.messages);
            if (newProps.status !== "DISABLED") {
                this.locate.drawMarker(this.locate._map);
            }
        }
    },
    onLocationError(err) {
        this.props.onLocateError(err.message);
        this.props.changeLocateState("DISABLED");
    },
    render() {
        return null;
    },
    defaultOpt: { // For all configuration options refer to https://github.com/Norkart/Leaflet-MiniMap
            follow: true,  // follow with zoom and pan the user's location
            remainActive: true,
            stopFollowingOnDrag: true,
            locateOptions: {
                maximumAge: 2000,
                enableHighAccuracy: false,
                timeout: 10000,
                maxZoom: Infinity,
                watch: true  // if you overwrite this, visualization cannot be updated
                }
            },
    locateControlState(state) {
        if (state.state === 'requesting' && this.props.status !== "LOCATING" ) {
            this.props.changeLocateState("LOCATING");
        }else if (state.state === 'following' && !this.fol ) {
            this.props.changeLocateState("FOLLOWING");
        }else if (state.state === 'active' && this.props.status !== "ENABLED" ) {
            this.props.changeLocateState("ENABLED");
        }
    }
});

module.exports = Locate;
