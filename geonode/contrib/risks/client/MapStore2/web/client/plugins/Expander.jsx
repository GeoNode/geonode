/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {Glyphicon} = require('react-bootstrap');
const assign = require('object-assign');

const Message = require('../components/I18N/Message');

const ExpanderPlugin = require('../components/buttons/ToggleButton');

module.exports = {
    ExpanderPlugin: assign(ExpanderPlugin, {
        Toolbar: {
            name: 'expand',
            position: 10000,
            alwaysVisible: true,
            tooltip: "expandtoolbar.tooltip",
            icon: <Glyphicon glyph="option-horizontal"/>,
            help: <Message msgId="helptexts.expandToolbar"/>,
            toggle: true,
            toggleControl: 'toolbar',
            toggleProperty: 'expanded',
            priority: 1
        }
    }),
    reducers: {}
};
