/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Radio} = require('react-bootstrap');
const LocaleUtils = require('../../utils/LocaleUtils');

const PrintOptions = React.createClass({
    propTypes: {
        layouts: React.PropTypes.array,
        enableRegex: React.PropTypes.oneOfType([React.PropTypes.object, React.PropTypes.string]),
        options: React.PropTypes.array,
        onChange: React.PropTypes.func,
        selected: React.PropTypes.string,
        isEnabled: React.PropTypes.func
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            layouts: [],
            enableRegex: /^.*$/,
            options: [{label: 'Option1', value: 'Option1'}, {label: 'Option2', value: 'Option2'}],
            onChange: () => {},
            selected: 'Option1'
        };
    },
    onChange(e) {
        this.props.onChange(e.target.value);
    },
    renderOptions() {
        return this.props.options.map((option) => <Radio
            key={option.label}
            disabled={!this.isEnabled()} ref={"input" + option.value}
            checked={this.props.selected === option.value}
            onChange={this.onChange}
            value={option.value}
        >{LocaleUtils.getMessageById(this.context.messages, option.label)}</Radio>);
    },
    render() {
        return (
            <span className="form-inline">
                {this.renderOptions()}
            </span>
        );
    },
    isEnabled() {
        return this.props.isEnabled ?
            this.props.isEnabled(this.props.layouts) :
            this.props.layouts.length === 0 || this.props.layouts.some((layout) => layout.name.match(this.props.enableRegex));
    }
});

module.exports = PrintOptions;
