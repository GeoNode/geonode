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

const {onCreateSnapshot, changeSnapshotState, saveImage, onRemoveSnapshot, onSnapshotError} = require('../actions/snapshot');

const {mapSelector} = require('../selectors/map');
const {layersSelector} = require('../selectors/layers');

const {toggleControl} = require('../actions/controls');

const assign = require('object-assign');
const Message = require('./locale/Message');
const {Glyphicon} = require('react-bootstrap');

const snapshotSelector = createSelector([
    mapSelector,
    layersSelector,
    (state) => state.controls && state.controls.toolbar && state.controls.toolbar.active === "snapshot" || state.controls.snapshot && state.controls.snapshot.enabled,
    (state) => state.browser,
    (state) => state.snapshot || {queue: []}
], (map, layers, active, browser, snapshot) => ({
    map,
    layers,
    active,
    browser,
    snapshot
}));

const SnapshotPanel = connect(snapshotSelector, {
    onCreateSnapshot: onCreateSnapshot,
    onStatusChange: changeSnapshotState,
    downloadImg: saveImage,
    toggleControl: toggleControl.bind(null, 'snapshot', null)
})(require("../components/mapcontrols/Snapshot/SnapshotPanel"));

const SnapshotPlugin = connect((state) => ({
    queue: state.snapshot && state.snapshot.queue || []
}), {
    downloadImg: saveImage,
    onSnapshotError,
    onRemoveSnapshot
})(require("../components/mapcontrols/Snapshot/SnapshotQueue"));


module.exports = {
    SnapshotPlugin: assign(SnapshotPlugin, {
        Toolbar: {
            name: 'snapshot',
            position: 8,
            panel: SnapshotPanel,
            help: <Message msgId="helptexts.snapshot"/>,
            tooltip: "snapshot.tooltip",
            icon: <Glyphicon glyph="camera"/>,
            wrap: true,
            title: "snapshot.title",
            exclusive: true,
            priority: 1
        },
        BurgerMenu: {
            name: 'snapshot',
            position: 3,
            panel: SnapshotPanel,
            text: <Message msgId="snapshot.title"/>,
            icon: <Glyphicon glyph="camera"/>,
            action: toggleControl.bind(null, 'snapshot', null),
            tools: [SnapshotPlugin],
            priority: 2
        }
    }),
    reducers: {
        snapshot: require('../reducers/snapshot')
    }
};
