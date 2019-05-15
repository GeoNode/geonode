/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {connect} = require('react-redux');

const {changeLocateState} = require('../actions/locate');

const Message = require('./locale/Message');

const {Glyphicon} = require('react-bootstrap');

const assign = require('object-assign');

const LocatePlugin = connect((state) => ({
    locate: state.locate && state.locate.state || 'DISABLED'
}), {
    onClick: changeLocateState
})(require('../components/mapcontrols/locate/LocateBtn'));

require('./locate/locate.css');

module.exports = {
    LocatePlugin: assign(LocatePlugin, {
        Toolbar: {
            name: 'locate',
            position: 2,
            tool: true,
            tooltip: "locate.tooltip",
            icon: <Glyphicon glyph="screenshot"/>,
            help: <Message msgId="helptexts.locateBtn"/>,
            priority: 1
        }
    }),
    reducers: {locate: require('../reducers/locate')}
};
