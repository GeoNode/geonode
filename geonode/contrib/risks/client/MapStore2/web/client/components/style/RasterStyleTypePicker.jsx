/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const Combobox = require('react-widgets').Combobox;

const LocaleUtils = require('../../utils/LocaleUtils');

const RasterStyleTypePicker = React.createClass({
    propTypes: {
        styletype: React.PropTypes.oneOf(['rgb', 'gray', 'pseudo']),
        onChange: React.PropTypes.func
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    render() {
        return (
            <Combobox data={[
                {
                    value: "rgb",
                    name: LocaleUtils.getMessageById(this.context.messages, "rasterstyletype.rgb"),
                    type: LocaleUtils.getMessageById(this.context.messages, "rasterstyletype.multi")
                },
                {
                    value: "gray",
                    name: LocaleUtils.getMessageById(this.context.messages, "rasterstyletype.gray"),
                    type: LocaleUtils.getMessageById(this.context.messages, "rasterstyletype.single")
                },
                {value: "pseudo",
                    name: LocaleUtils.getMessageById(this.context.messages, "rasterstyletype.pseudo"),
                    type: LocaleUtils.getMessageById(this.context.messages, "rasterstyletype.single")
                }]}
                textField="name"
                valueField="value"
                groupBy="type"
                onChange={(v) => this.props.onChange("styletype", v.value)}
                value={this.props.styletype} />
            );
    }
});

module.exports = RasterStyleTypePicker;
