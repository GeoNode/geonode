/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {connect} = require('react-redux');
const {mapSelector} = require('../selectors/map');
const {createSelector} = require('reselect');

const assign = require('object-assign');

const {changeMousePositionCrs, changeMousePositionState} = require('../actions/mousePosition');

const getDesiredPosition = (map, mousePosition, mapInfo) => {
    if (mousePosition.showCenter && map) {
        return map.center;
    }
    if (mousePosition.showOnClick) {
        if (mapInfo.clickPoint && mapInfo.clickPoint.latlng) {
            return {
                x: mapInfo.clickPoint.latlng.lng,
                y: mapInfo.clickPoint.latlng.lat,
                crs: "EPSG:4326"
            };
        }
        return {
            crs: "EPSG:4326"
        };
    }
    return mousePosition.position;
};

const selector = createSelector([
    mapSelector,
    (state) => state.mousePosition || {},
    (state) => state.mapInfo || {}
], (map, mousePosition, mapInfo) => ({
    enabled: mousePosition.enabled,
    mousePosition: getDesiredPosition(map, mousePosition, mapInfo),
    crs: mousePosition.crs || map && map.projection || 'EPSG:3857'
}));

const Message = require('./locale/Message');

const CRSSelector = connect((state) => ({
    crs: state.mousePosition && state.mousePosition.crs || state.map && state.map.present && state.map.present.projection || 'EPSG:3857'
}), {
    onCRSChange: changeMousePositionCrs
})(require('../components/mapcontrols/mouseposition/CRSSelector'));

const MousePositionButton = connect((state) => ({
    pressed: state.mousePosition && state.mousePosition.enabled,
    active: state.mousePosition && state.mousePosition.enabled,
    pressedStyle: "default",
    defaultStyle: "primary",
    btnConfig: {
        bsSize: "small"}
}), {
    onClick: changeMousePositionState
})(require('../components/buttons/ToggleButton'));

const MousePositionPlugin = connect(selector)(require('../components/mapcontrols/mouseposition/MousePosition'));

module.exports = {
    MousePositionPlugin: assign(MousePositionPlugin, {
        Settings: {
            tool: <div id="mapstore-mousepositionsettings" key="mousepositionsettings">
            <CRSSelector
                key="crsSelector"
                enabled={true}
                label={<Message msgId="mousePositionCoordinates" />}
            />
            <MousePositionButton
                key="mousepositionbutton"
                isButton={true}
                text={<Message msgId="showMousePositionCoordinates" />}
            />
            </div>,
            position: 2
        }
    }),
    reducers: {mousePosition: require('../reducers/mousePosition')}
};
