/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');

const Slider = require('react-nouislider');

require("react-nouislider/example/nouislider.css");
require("./opacitypicker.css");

const OpacityPicker = React.createClass({
    propTypes: {
        opacity: React.PropTypes.oneOfType([React.PropTypes.number, React.PropTypes.string]),
        onChange: React.PropTypes.func,
        disabled: React.PropTypes.bool
    },
    getDefaultProps() {
        return {
            opacity: "1",
            onChange: () => {},
            disabled: false
        };
    },
    render() {
        return (
            <div className="opacity-picker">
                <Slider
                    disabled={this.props.disabled}
                    start={[this.props.opacity * 100 ]}
                    range={{min: 0, max: 100}}
                    onChange={(v) => this.props.onChange("opacity", (v / 100).toFixed(2))}
                    connect="lower"
                    tooltips={[ {
                        to: function( value ) {
                            return Math.round(value) + '%';
                        }
                        }
                        ]}
                />
            </div>);
    }
});

module.exports = OpacityPicker;
