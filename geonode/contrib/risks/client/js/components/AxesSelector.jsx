/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const Nouislider = require('react-nouislider');
const {connect} = require('react-redux');
const {show, hide} = require('react-notification-system-redux');
const {labelSelector} = require('../selectors/disaster');
const {getSFurtherResourceData} = require('../actions/disaster');
const LabelResource = connect(labelSelector, { show, hide, getData: getSFurtherResourceData })(require('../components/LabelResource'));

const AxesSelector = React.createClass({
    propTypes: {
        dimension: React.PropTypes.object,
        activeAxis: React.PropTypes.number,
        setDimIdx: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            activeAxis: 0,
            setDimIdx: () => {}
        };
    },
    render() {
        const {name = '', values = []} = this.props.dimension || {};
        const label = !this.props.dimension ? null : (<LabelResource uid={'map_label_tab'} label={name + ': ' + values[this.props.activeAxis]} dimension={this.props.dimension}/>);
        return !this.props.dimension || values.length - 1 === 0 ? label : (
            <div className="text-center">
                <LabelResource uid={'map_label_tab'} label={name + ': ' + values[this.props.activeAxis]} dimension={this.props.dimension}/>
                <div className="slider-box">
                    <Nouislider
                        range={{min: 0, max: values.length - 1}}
                        start={[this.props.activeAxis]}
                        step={1}
                        tooltips={false}
                        onChange={(idx) => this.props.setDimIdx('dim2Idx', Number.parseInt(idx[0]))}
                        pips= {{
                            mode: 'steps',
                            density: 20,
                            format: {
                                to: (value) => {
                                    let val = values[value].split(" ")[0];
                                    return val.length > 8 ? val.substring(0, 8) + '...' : val;
                                },
                                from: (value) => {
                                    return value;
                                }
                            }
                        }}
                    />
                </div>
            </div>
        );
    }
});

module.exports = AxesSelector;
