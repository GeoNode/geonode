/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const { SketchPicker } = require('react-color');
require('./colorenderer.css');
const {getWindowSize} = require('../../../utils/AgentUtils');
const ColorPickerRenderer = React.createClass({
    propTypes: {
        params: React.PropTypes.object,
        onChangeColor: React.PropTypes.func,
        disabled: React.PropTypes.bool
    },
    getInitialState() {
        return {
            displayColorPicker: false
        };
    },
    getDefaultProps() {
        return {
          disabled: false,
            onChangeColor: () => {}
        };
    },
    onChangeColor() {
        if ( this.state.color) {
            let opacity = (this.state.color.rgb.a !== 1) ? this.state.color.rgb.a : undefined;
            let color = this.state.color.hex.indexOf("#") === 0 ? this.state.color.hex : "#" + this.state.color.hex;
            this.props.onChangeColor( this.props.params.node, {color: color, opacity: opacity});
        }
    },
    getBackgroundColor(data) {
        let color = 'blue';
        if ( data && data.color) {
            let rgb = this.hexToRgb(data.color);
            let opacity = (data.opacity !== undefined) ? data.opacity : 1;
            color = (rgb) ? `rgba(${ rgb.r }, ${ rgb.g }, ${ rgb.b }, ${ opacity })` : 'blue';
        }
        return (color);
    },
    render() {
        let data = this.props.params.data;
        let colorValue = ( data && data.color) ? this.hexToRgb(data.color) : {r: 0, g: 0, b: 255};
        colorValue.a = (data.opacity !== undefined) ? data.opacity : 1;
        let bkgColor = this.getBackgroundColor(data);
        return (
            <div>
                <div className="cpr-color"
                style={{ backgroundColor: bkgColor}}
                onClick={ (e) => {
                    if (!this.props.disabled) {
                        this.setState({
                        displayColorPicker: !this.state.displayColorPicker,
                        y: e.pageY
                    }); }
                }}
                />
                { this.state.displayColorPicker ? (
                    <div className="cpe-popover" style={{top: this.calculateTop(this.state.y)}}>
                    <div className="cpe-cover" onClick={ () => {
                        this.setState({ displayColorPicker: false});
                        this.onChangeColor();
                    }}/>
                        <SketchPicker
                            color={ (this.state.color) ? this.state.color.rgb : colorValue}
                            onChangeComplete={ (color) => { this.setState({ color: color }); }} />
                    </div>)
                : null }
            </div>
        );
    },
    calculateTop(y) {
        let h = getWindowSize().maxHeight;
        return ((y + 300 > h) ? h - 305 : y ) - 300;
    },
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }
});

module.exports = ColorPickerRenderer;
