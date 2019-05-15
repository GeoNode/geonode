/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const Nouislider = require('react-nouislider');
const LabelResource = require('../components/LabelResource');

const ExtendedSlider = React.createClass({
    propTypes: {
        uid: React.PropTypes.string,
        dimension: React.PropTypes.object,
        activeAxis: React.PropTypes.number,
        maxLength: React.PropTypes.number,
        sliders: React.PropTypes.object,
        setDimIdx: React.PropTypes.func,
        chartSliderUpdate: React.PropTypes.func,
        dimIdx: React.PropTypes.string,
        color: React.PropTypes.string,
        currentUrl: React.PropTypes.string,
        show: React.PropTypes.func,
        hide: React.PropTypes.func,
        notifications: React.PropTypes.array,
        getData: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            uid: '',
            activeAxis: 0,
            maxLength: 25,
            sliders: {},
            setDimIdx: () => {},
            chartSliderUpdate: () => {},
            dimIdx: 'dim2Idx',
            dimensions: [],
            color: '#5d9bd1'
        };
    },
    getBrushData(data) {
        return data.map((val, idx) => { return {value: idx, name: val}; });
    },
    renderBrushSlider(data, label) {
        const startIndex = this.props.sliders[this.props.uid] ? this.props.sliders[this.props.uid].startIndex : 0;
        const endIndex = this.props.sliders[this.props.uid] ? this.props.sliders[this.props.uid].endIndex : this.props.maxLength - 1;
        return (
            <div className="text-center slider-box">
                <div className="disaster-chart-slider">
                    <Nouislider
                        range={{min: 0, max: data.length - 1}}
                        start={[startIndex, endIndex]}
                        limit={this.props.maxLength}
                        behaviour={'tap-drag'}
                        connect={true}
                        margin={5}
                        step={1}
                        tooltips={false}
                        onChange={(idx) =>
                            this.props.chartSliderUpdate({startIndex: Number.parseInt(idx[0]), endIndex: Number.parseInt(idx[1])}, this.props.uid)
                        }/>
                </div>
                {label}
                <Nouislider
                    range={{min: startIndex, max: endIndex}}
                    start={[this.props.activeAxis]}
                    step={1}
                    tooltips={false}
                    onChange={(idx) => this.props.setDimIdx(this.props.dimIdx, Number.parseInt(idx[0]))}
                    pips= {{
                        mode: 'steps',
                        density: 20,
                        format: {
                          to: this.formatTo,
                          from: this.formatFrom
                        }
                }}/>
            </div>
        );
    },
    renderSlider(data) {
        const {maxLength, currentUrl, show, hide, notifications, getData} = this.props;
        const {values = [], name} = this.props.dimension || {};
        const label = !this.props.dimension ? null : (
            <LabelResource
                uid={this.props.uid}
                label={name + ' ' + values[this.props.activeAxis]}
                dimension={this.props.dimension}
                currentUrl={currentUrl}
                show={show}
                hide={hide}
                notifications={notifications}
                getData={getData}
            />
        );
        return data.length > maxLength ? this.renderBrushSlider(data, label) : (
            <div className="text-center slider-box">
                {label}
                <Nouislider
                    range={{min: 0, max: data.length - 1}}
                    start={[this.props.activeAxis]}
                    step={1}
                    tooltips={false}
                    onChange={(idx) => this.props.setDimIdx(this.props.dimIdx, Number.parseInt(idx[0]))}
                    pips= {{
                        mode: 'steps',
                        density: 20,
                        format: {
                            to: this.formatTo,
                            from: this.formatFrom
                        }
                    }}/>
            </div>
        );
    },
    render() {
        const {values = []} = this.props.dimension || {};
        const slider = !this.props.dimension || values.length - 1 === 0 ? null : this.renderSlider(values);
        return (
            <div>
                {slider}
            </div>
        );
    },
    formatTo(value) {
        const {values = []} = this.props.dimension || {};
        let val = values[value].split(" ")[0];
        return val.length > 8 ? val.substring(0, 8) + '...' : val;
    },
    formatFrom(value) {
        return value;
    }
});

module.exports = ExtendedSlider;
