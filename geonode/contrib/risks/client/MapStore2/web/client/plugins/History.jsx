/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {connect} = require('react-redux');

const assign = require('object-assign');

const Message = require('./locale/Message');

const {Glyphicon} = require('react-bootstrap');

const { ActionCreators } = require('redux-undo');
const {undo, redo} = ActionCreators;

const UndoButton = connect((state) => {
    let mapHistory = state.map && state.map.past && {past: state.map.past, future: state.map.future} || {past: [], future: []};
    return {
        disabled: (mapHistory.past.length > 0) ? false : true
    };
}, {
    onClick: undo
})(require('../components/mapcontrols/navigationhistory/UndoButton'));

const RedoButton = connect((state) => {
    let mapHistory = state.map && state.map.past && {past: state.map.past, future: state.map.future} || {past: [], future: []};
    return {
        disabled: (mapHistory.future.length > 0) ? false : true
    };
}, {
    onClick: redo
})(require('../components/mapcontrols/navigationhistory/RedoButton'));

module.exports = {
    UndoPlugin: assign(UndoButton, {
        Toolbar: {
            name: 'undo',
            position: 5,
            tool: true,
            tooltip: "history.undoBtnTooltip",
            icon: <Glyphicon glyph="step-backward"/>,
            help: <Message msgId="helptexts.historyundo"/>,
            priority: 1
        }
    }),
    RedoPlugin: assign(RedoButton, {
        Toolbar: {
            name: 'redo',
            position: 6,
            tool: true,
            tooltip: "history.redoBtnTooltip",
            icon: <Glyphicon glyph="step-forward"/>,
            help: <Message msgId="helptexts.historyredo"/>,
            priority: 1
        }
    }),
    reducers: {}
};
