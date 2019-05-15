/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {connect} = require('react-redux');
const Debug = require('../../../components/development/Debug');

const Localized = require('../../../components/I18N/Localized');

const App = (props) => {
    const MapViewer = connect(() => ({
        plugins: props.plugins
    }))(require('../pages/MapViewer'));
    return (
        <div className="fill">
            <Localized messages={props.messages} locale={props.current} loadingError={props.localeError}>
               <MapViewer params={{mapType: "leaflet", mapId: "0"}} />
            </Localized>
            <Debug/>
        </div>
    );
};

module.exports = connect((state) => {
    return state.locale && {...state.locale} || {};
})(App);
