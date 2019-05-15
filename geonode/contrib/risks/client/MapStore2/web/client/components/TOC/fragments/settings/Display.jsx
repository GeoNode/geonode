/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');

const Slider = require('react-nouislider');
const {Label} = require('react-bootstrap');
const {DropdownList} = require('react-widgets');
const Message = require('../../../I18N/Message');
require('react-widgets/lib/less/react-widgets.less');
module.exports = React.createClass({
    propTypes: {
        opacityText: React.PropTypes.node,
        element: React.PropTypes.object,
        formats: React.PropTypes.array,
        settings: React.PropTypes.object,
        onChange: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            onChange: () => {}
        };
    },
    render() {
        return (<div>
            {this.props.element.type === "wms" ?
            [(<label key="format-label" className="control-label"><Message msgId="layerProperties.format" /></label>),
            (<DropdownList
                key="format-dropdown"
                data={this.props.formats || ["image/png", "image/png8", "image/jpeg", "image/vnd.jpeg-png", "image/gif"]}
                value={this.props.element && this.props.element.format || "image/png"}
                onChange={(value) => {
                    this.props.onChange("format", value);
                }} />)] : null}
            <div key="opacity">
            <label key="opacity-label" className="control-label">{this.props.opacityText}</label>
            <Slider key="opacity-slider" start={[Math.round(this.props.settings.options.opacity * 100)]}
                range={{min: 0, max: 100}}
                onChange={(opacity) => {this.props.onChange("opacity", opacity / 100); }}/>
            <Label key="opacity-percent" >{Math.round(this.props.settings.options.opacity * 100) + "%"}</Label>
            </div>
            {this.props.element.type === "wms" ?
                [(<div key="transparent-check"><input type="checkbox" key="transparent" checked={this.props.element && (this.props.element.transparent === undefined ? true : this.props.element.transparent)}
                onChange={(event) => {this.props.onChange("transparent", event.target.checked); }}/>
            <label key="transparent-label" className="control-label">Transparent</label></div>)] : null}
        </div>);
    }
});
