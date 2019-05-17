/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {LineChart, ReferenceDot, ReferenceLine, Line, XAxis, Tooltip, YAxis, CartesianGrid, ResponsiveContainer} = require('recharts');
const {Panel} = require('react-bootstrap');
const ChartTooltip = require("./ChartTooltip");
const Nouislider = require('react-nouislider');

const CustomizedYLable = (props) => {
    const {y, lab, viewBox} = props;
    return (
        <g>
            <text x={viewBox.width / 2} y={y} dy={-25} dx={0} textAnchor="middle" fill="#666" transform="rotate(0)">{lab}</text>
        </g>
    );
};

const SliderChart = React.createClass({
    propTypes: {
        uid: React.PropTypes.string,
        labelUid: React.PropTypes.string,
        type: React.PropTypes.string,
        dimension: React.PropTypes.array,
        dim: React.PropTypes.object,
        values: React.PropTypes.array,
        val: React.PropTypes.string,
        uOm: React.PropTypes.string,
        maxLength: React.PropTypes.number,
        sliders: React.PropTypes.object,
        setDimIdx: React.PropTypes.func,
        chartSliderUpdate: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            uid: '',
            labelUid: '',
            type: 'line',
            maxLength: 25,
            sliders: {},
            setDimIdx: () => {},
            chartSliderUpdate: () => {}
        };
    },
    getChartData() {
        const {dim, values, val} = this.props;
        return values.filter((d) => d[dim.dim1] === val ).map((v) => {return {"name": v[dim.dim2], "value": parseFloat(v[2], 10)}; });
    },
    renderChart(chartData) {
        const {dim, dimension, uOm} = this.props;
        return (
            <Panel className="panel-box">
                <h4 className="text-center">{dimension[dim.dim1].name + ' ' + dimension[dim.dim1].values[dim.dim1Idx]}</h4>
                <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={chartData} onClick={this.handleClick} margin={{top: 20, right: 30, left: 30, bottom: 5}}>
                        <XAxis interval="preserveStartEnd" dataKey="name" tickFormatter={this.formatXTiks}/>
                        <Tooltip content={<ChartTooltip xAxisLabel={dimension[dim.dim2].name} xAxisUnit={dimension[dim.dim2].unit} uOm={uOm}/>}/>
                        <YAxis label={<CustomizedYLable lab={uOm}/>} interval="preserveStart" tickFormatter={this.formatYTiks}/>
                        <CartesianGrid horizontal={false} strokeDasharray="3 3"/>
                        <Line type="monotone" dataKey="value" stroke="#ff8f31" strokeWidth={2}/>
                        <ReferenceDot isFront={true} y={chartData[dim.dim2Idx].value} x={chartData[dim.dim2Idx].name} r={8} stroke={'#2c689c'} fill="none" />
                    </LineChart>
                </ResponsiveContainer>
            </Panel>
        );
    },
    renderChartSlider(chartData, startIndex, endIndex) {
        const {dim, dimension, uOm} = this.props;
        const sectionData = chartData.slice(startIndex, endIndex + 1);
        return (
            <div className="disaster-chart-slider">
                <Panel className="panel-box">
                    <h4 className="text-center">{dimension[dim.dim1].name + ' ' + dimension[dim.dim1].values[dim.dim1Idx]}</h4>
                    <ResponsiveContainer width="100%" height={220}>
                        <LineChart data={sectionData} onClick={this.handleClick} margin={{top: 50, right: 30, left: 30, bottom: 5}}>
                            <XAxis interval="preserveStartEnd" dataKey="name" tickFormatter={this.formatXTiks}/>
                            <Tooltip content={<ChartTooltip xAxisLabel={dimension[dim.dim2].name} xAxisUnit={dimension[dim.dim2].unit} uOm={uOm}/>}/>
                            <YAxis label={<CustomizedYLable lab={uOm}/>} interval="preserveStart" tickFormatter={this.formatYTiks}/>
                            <CartesianGrid horizontal={false} strokeDasharray="3 3"/>
                            <Line type="monotone" dataKey="value" stroke="#ff8f31" strokeWidth={2} isAnimationActive={false}/>
                            <ReferenceDot isFront={true} y={chartData[dim.dim2Idx].value} x={chartData[dim.dim2Idx].name} r={8} stroke={'#2c689c'} fill="none" />
                            <ReferenceLine strokeDasharray="10, 5" isFront={true} x={chartData[startIndex].name} stroke={'#333'} strokeWidth={4}/>
                            <ReferenceLine strokeDasharray="10, 5" isFront={true} x={chartData[endIndex].name} stroke={'#333'} strokeWidth={4}/>
                        </LineChart>
                    </ResponsiveContainer>
                    <ResponsiveContainer width="100%" height={100}>
                        <LineChart data={chartData}>
                            <Line dot={false} type="monotone" dataKey="value" stroke="#ff8f31" strokeWidth={1} isAnimationActive={false}/>
                            <XAxis interval="preserveStartEnd" dataKey="name" tickFormatter={this.formatXTiks}/>
                            <YAxis axisLine={false} tickLine={false} tick={false} interval="preserveStart" mirror={true}/>
                            <ReferenceDot isFront={true} y={chartData[dim.dim2Idx].value} x={chartData[dim.dim2Idx].name} r={4} stroke={'#2c689c'} fill="none" />
                            <ReferenceLine strokeDasharray="6, 3" isFront={true} x={chartData[startIndex].name} stroke={'#333'} strokeWidth={1}/>
                            <ReferenceLine strokeDasharray="6, 3" isFront={true} x={chartData[endIndex].name} stroke={'#333'} strokeWidth={1}/>
                        </LineChart>
                    </ResponsiveContainer>
                    <Nouislider
                        range={{min: 0, max: chartData.length - 1}}
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
                </Panel>
            </div>
        );
    },
    render() {
        const {maxLength} = this.props;
        const chartData = this.getChartData();
        const startIndex = this.props.sliders[this.props.uid] ? this.props.sliders[this.props.uid].startIndex : 0;
        const endIndex = this.props.sliders[this.props.uid] ? this.props.sliders[this.props.uid].endIndex : this.props.maxLength - 1;
        const chart = chartData.length > maxLength ? this.renderChartSlider(chartData, startIndex, endIndex) : this.renderChart(chartData);
        return (
            <div>
                {chart}
            </div>
        );
    },
    formatYTiks(v) {
        return v.toLocaleString();
    },
    handleClick(data) {
        if (data && this.props.dimension) {
            this.props.setDimIdx('dim2Idx', this.props.dimension[this.props.dim.dim2].values.indexOf(data.activeLabel));
        }
    },
    formatXTiks(v) {
        return !isNaN(v) && parseFloat(v).toLocaleString() || v;
    }
});

module.exports = SliderChart;

