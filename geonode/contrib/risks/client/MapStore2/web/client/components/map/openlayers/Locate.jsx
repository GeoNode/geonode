/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 *
 */

var React = require('react');
var OlLocate = require('../../../utils/openlayers/OlLocate');

var Locate = React.createClass({
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
        if (this.props.map) {
            this.locate = new OlLocate(this.props.map, this.defaultOpt);
            this.locate.options.onLocationError = this.onLocationError;
            this.locate.on("propertychange", (e) => {this.onStateChange(e.target.get(e.key)); });
        }
    },
    componentWillReceiveProps(newProps) {
        let state = this.locate.get("state");
        if (newProps.status !== this.props.status) {
            if ( newProps.status === "ENABLED" && state === "DISABLED") {
                this.locate.start();
            }else if (newProps.status === "FOLLOWING" && state === "ENABLED") {
                this.locate.startFollow();
            }else if (newProps.status === "DISABLED") {
                this.locate.stop();
            }
        }
        if (newProps.messages !== this.props.messages) {
            this.locate.setStrings(newProps.messages);
        }
    },
    onStateChange(state) {
        if (this.props.status !== state) {
            this.props.changeLocateState(state);
        }
    },
    onLocationError(err) {
        this.props.onLocateError(err.message);
        this.props.changeLocateState("DISABLED");
    },
    render() {
        return null;
    },
    defaultOpt: {
        follow: true,// follow with zoom and pan the user's location
        remainActive: true,
        metric: true,
        stopFollowingOnDrag: true,
        keepCurrentZoomLevel: false,
        locateOptions: {
            maximumAge: 2000,
            enableHighAccuracy: false,
            timeout: 10000,
            maxZoom: 18
        }
    }
});

module.exports = Locate;
