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
// TODO: make step and glyphicon configurable
const selector = createSelector([mapSelector], (map) => ({currentZoom: map && map.zoom, id: "zoomin-btn", step: 1, glyphicon: "plus"}));

const {changeZoomLevel} = require('../actions/map');

const Message = require('../components/I18N/Message');

const ZoomInButton = connect(selector, {
    onZoom: changeZoomLevel
})(require('../components/buttons/ZoomButton'));

require('./zoom/zoom.css');

const assign = require('object-assign');


module.exports = {
    ZoomInPlugin: assign(ZoomInButton, {
        Toolbar: {
            name: "ZoomIn",
            position: 3,
            tooltip: "zoombuttons.zoomInTooltip",
            help: <Message msgId="helptexts.zoomIn"/>,
            tool: true,
            priority: 1
        }
    }),
    reducers: { zoomIn: require("../reducers/map")}
};
