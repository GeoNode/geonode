/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const DropdownList = require('react-widgets').DropdownList;
const LocaleUtils = require('../../utils/LocaleUtils');
const MarkNameSelector = React.createClass({
    propTypes: {
        markName: React.PropTypes.string,
        onChange: React.PropTypes.func
    },
    contextTypes: {
        messages: React.PropTypes.object

    },
    getDefaultProps() {
        return {
            markName: "circle",
            onChange: () => {}
        };
    },
    render() {
        return (
            <DropdownList data={
                [
                    {value: "circle", name: LocaleUtils.getMessageById(this.context.messages, "markNameSelector.circle") || "Circle"},
                    {value: 'square', name: LocaleUtils.getMessageById(this.context.messages, "markNameSelector.square") || "Square"},
                    {value: 'triangle', name: LocaleUtils.getMessageById(this.context.messages, "markNameSelector.triangle") || "Triangle"},
                    {value: 'star', name: LocaleUtils.getMessageById(this.context.messages, "markNameSelector.star") || "Star"},
                    {value: 'cross', name: LocaleUtils.getMessageById(this.context.messages, "markNameSelector.cross") || "Cross"},
                    {value: 'x', 'name': LocaleUtils.getMessageById(this.context.messages, "markNameSelector.x") || "X"}
                ]}
                valueField="value"
                textField="name"
                value={this.props.markName}
                onChange={(v) => this.props.onChange("markName", v.value)}/>);
    }
});

module.exports = MarkNameSelector;
