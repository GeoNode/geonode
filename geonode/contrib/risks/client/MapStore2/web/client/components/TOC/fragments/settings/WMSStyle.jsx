/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
const Message = require('../../../I18N/Message');
const Select = require('react-select');
const {Button, Glyphicon, Alert} = require('react-bootstrap');
const {findIndex} = require('lodash');

require('react-select/dist/react-select.css');

/**
 * General Settings form for layer
 */
const WMSStyle = React.createClass({
    propTypes: {
        retrieveLayerData: React.PropTypes.func,
        updateSettings: React.PropTypes.func,
        element: React.PropTypes.object,
        groups: React.PropTypes.array
    },
    getDefaultProps() {
        return {
            element: {},
            retrieveLayerData: () => {},
            updateSettings: () => {}
        };
    },
    renderLegend() {
        // legend can not added because of this issue
        // https://github.com/highsource/ogc-schemas/issues/183
        return null;
    },
    renderItemLabel(item) {
        return (<div>
            <div key="item-title">{item.title || item.name}</div>
            <div><small className="text-muted"key="item-key-description">{item.name}</small></div>
        </div>);
    },
    renderError() {
        if (this.props.element && this.props.element.capabilities && this.props.element && this.props.element.capabilities.error) {
            return <Alert bsStyle="danger"><Message msgId="layerProperties.styleListLoadError" /></Alert>;
        }
    },
    render() {
        let options = [{label: "Default Style", value: ""}].concat((this.props.element.availableStyles || []).map((item) => {
            return {label: this.renderItemLabel(item), value: item.name};
        }));
        let currentStyleIndex = this.props.element.style && this.props.element.availableStyles && findIndex(this.props.element.availableStyles, el => el.name === this.props.element.style);
        if (!(currentStyleIndex >= 0) && this.props.element.style) {
            options.push({label: this.props.element.style, value: this.props.element.style });
        }
        return (<form ref="style">
            <Select.Creatable
                    key="styles-dropdown"
                    options={options}
                    isLoading={this.props.element && this.props.element.capabilitiesLoading}
                    value={this.props.element.style || ""}
                    onOpen={() => {
                        // automatic retrieve if availableStyles are not available or capabilities is not present
                        // that means you don't have a list and you didn't try to load it.
                        if (this.props.element && !(this.props.element.capabilities && this.props.element.availableStyles)) {
                            this.props.retrieveLayerData(this.props.element);
                        }
                    }}
                    promptTextCreator={(value) => {
                        return <Message msgId="layerProperties.styleCustom" msgParams={{value}} />;
                    }}
                    onChange={(selected) => {
                        this.updateEntry("style", {target: {value: (selected && selected.value) || ""}});
                    }}
                    />
                <br />
                {this.renderLegend()}
                {this.renderError()}
                <Button bsStyle="primary" style={{"float": "right"}} onClick={() => this.props.retrieveLayerData(this.props.element)}><Glyphicon glyph="refresh" />&nbsp;<Message msgId="layerProperties.stylesRefreshList" /></Button>
                <br />
            </form>);
    },
    updateEntry(key, event) {
        let value = event.target.value;
        this.props.updateSettings({[key]: value});
    }
});

module.exports = WMSStyle;
