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

const {mapSelector} = require('../selectors/map');
const {layersSelector} = require('../selectors/layers');

const {getFeatureInfo, getVectorInfo, purgeMapInfoResults, showMapinfoMarker, hideMapinfoMarker, showMapinfoRevGeocode, hideMapinfoRevGeocode} = require('../actions/mapInfo');
const {changeMousePointer} = require('../actions/map');
const {changeMapInfoFormat} = require('../actions/mapInfo');

const Message = require('./locale/Message');

const {Glyphicon} = require('react-bootstrap');

const assign = require('object-assign');

require('./identify/identify.css');

const selector = createSelector([
    (state) => (state.mapInfo && state.mapInfo.enabled) || (state.controls && state.controls.info && state.controls.info.enabled) || false,
    (state) => state.mapInfo && state.mapInfo.responses || [],
    (state) => state.mapInfo && state.mapInfo.requests || [],
    (state) => state.mapInfo && state.mapInfo.infoFormat,
    mapSelector,
    layersSelector,
    (state) => state.mapInfo && state.mapInfo.clickPoint,
    (state) => state.mapInfo && state.mapInfo.showModalReverse,
    (state) => state.mapInfo && state.mapInfo.reverseGeocodeData

], (enabled, responses, requests, format, map, layers, point, showModalReverse, reverseGeocodeData) => ({
    enabled, responses, requests, format, map, layers, point, showModalReverse, reverseGeocodeData
}));
// result panel

/**
 * Identify plugin. This plugin allows to perform getfeature info.
 * It can be configured to have a mobile or a desktop flavor.
 * @class Identify
 * @memberof plugins
 * @static
 *
 * @prop showIn {string[]} List of the plugins where to show the plugin
 * @prop bodyClass {string} class to assign to the feature info panel body
 * @prop cfg.style {object} inline css style
 * @prop cfg.draggable {boolean} draggable info window
 * @prop cfg.collapsible {boolean} collapsible info panel
 * @prop cfg {object} style
 * @prop cfg.viewerOptions {object}
 * @prop cfg.viewerOptions.container {expression} the container of the viewer, expression from the context
 * @prop cfg.viewerOptions.header {expression} the geader of the viewer, expression from the context{expression}
 * @prop cfg.viewerOptions.collapsible {boolean} the single feature viewer is collapsible
 *
 * @example
 * {
 *   "name": "Identify",
 *   "showIn": ["Settings"],
 *   "cfg": {
 *       "style": {
 *           "position": "absolute",
 *           "width": "100%",
 *           "bottom": "0px",
 *           "zIndex": 1023,
 *           "maxHeight": "70%",
 *           "marginBottom": 0
 *       },
 *       "draggable": false,
 *       "collapsible": true,
 *       "viewerOptions": {
 *       "container": "{context.ReactSwipe}",
 *       "header": "{context.SwipeHeader}",
 *       "collapsible": false
 *   },
 *   "bodyClass": "mobile-feature-info"
 *  }
 * }
 */
const IdentifyPlugin = connect(selector, {
    sendRequest: getFeatureInfo,
    localRequest: getVectorInfo,
    purgeResults: purgeMapInfoResults,
    changeMousePointer,
    showMarker: showMapinfoMarker,
    hideMarker: hideMapinfoMarker,
    showRevGeocode: showMapinfoRevGeocode,
    hideRevGeocode: hideMapinfoRevGeocode
})(require('../components/data/identify/Identify'));
// configuration UI
const FeatureInfoFormatSelector = connect((state) => ({
    infoFormat: state.mapInfo && state.mapInfo.infoFormat
}), {
    onInfoFormatChange: changeMapInfoFormat
})(require("../components/misc/FeatureInfoFormatSelector"));

module.exports = {
    IdentifyPlugin: assign(IdentifyPlugin, {
        Toolbar: {
            name: 'info',
            position: 6,
            tooltip: "info.tooltip",
            icon: <Glyphicon glyph="map-marker"/>,
            help: <Message msgId="helptexts.infoButton"/>,
            toggle: true
        },
        Settings: {
            tool: <FeatureInfoFormatSelector
                key="featureinfoformat"
                label={<Message msgId="infoFormatLbl" />
            }/>,
            position: 3
        }
    }),
    reducers: {mapInfo: require('../reducers/mapInfo')}
};
