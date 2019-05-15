/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {connect} = require('react-redux');

const MessagePlugin = connect((state) => ({
    content: state.my.content
}))((props) => (props.content ? <div className="myMessage" style={props.style}>{props.content}</div> : <span/>));

module.exports = {
    MessagePlugin,
    reducers: {}
};
