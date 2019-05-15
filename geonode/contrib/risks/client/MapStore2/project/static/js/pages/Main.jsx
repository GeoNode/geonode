/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {connect} = require('react-redux');
const {loadMapConfig} = require('../../MapStore2/web/client/actions/config');

const MapViewer = connect(() => ({}), {
    loadMapConfig: loadMapConfig.bind(null, "config.json", false)
})(require('../../MapStore2/web/client/containers/MapViewer'));

const Main = (props) => <MapViewer plugins={props.plugins} params={{mapType: "leaflet"}}/>;

module.exports = Main;
