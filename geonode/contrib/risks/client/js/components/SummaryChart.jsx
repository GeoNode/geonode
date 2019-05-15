/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Cell, Bar, BarChart, Legend, LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer} = require('recharts');
const chromaJs = require('chroma-js');
const {Panel} = require('react-bootstrap');

const CustomizedYLable = (props) => {
    const {x, y, lab} = props;
    return (
        <g className="recharts-cartesian-axis-label">
            <text x={x} y={y} dy={-10} dx={56} textAnchor="middle" fill="#666" transform="rotate(0)" className="recharts-text">{lab}</text>
        </g>
    );
};

const SummaryChart = React.createClass({
    propTypes: {
        values: React.PropTypes.array,
        dimension: React.PropTypes.array,
        dim: React.PropTypes.object,
        val: React.PropTypes.string,
        uOm: React.PropTypes.string
    },
    getDefaultProps() {
        return {
        };
    },
    getChartData() {
        const {dim, values, dimension} = this.props;
        return dimension[dim.dim2].values
        .filter((val) => {
            return val !== 'AED';
        })
        .map((val) => {
            return values.filter((d) => d[dim.dim2] === val);
        }).map((v) => {
            return v.reduce((a, b, idx) => {
                let aV = idx === 0 ? {name: a[dim.dim2]} : a;
                let obj = {}; obj[b[dim.dim1]] = parseFloat(b[2], 10);
                return Object.assign({}, obj, aV);
            }, v[0]);
        });
    },
    getAED() {
        const {values} = this.props;
        return values.filter((val) => {
            return val[1] === 'AED';
        })
        .map((val) => {
            return {name: val[0], value: parseFloat(val[2])};
        });
    },
    getLines() {
        const {dim, dimension, val} = this.props;
        const colors = chromaJs.scale('YlGnBu').mode('lch').colors(dimension[dim.dim1].values.length);
        return dimension[dim.dim1].values.map((v, idx) => {
            return val === v ? (<Line key={idx} type="monotone" dataKey={v} stroke="#ff8f31" strokeWidth={2}/>) : (<Line key={idx} type="monotone" dataKey={v} stroke={colors[idx]}/>);
        });
    },
    getBars() {
        const {dim, dimension, val} = this.props;
        const colors = chromaJs.scale('YlGnBu').mode('lch').colors(dimension[dim.dim1].values.length);
        return dimension[dim.dim1].values.map((v, idx) => {
            return val === v ? (<Bar key={idx} type="monotone" dataKey={v} stroke="#ff8f31" strokeWidth={2}/>) : (<Bar key={idx} type="monotone" dataKey={v} stroke={colors[idx]}/>);
        });
    },
    render() {
        const {uOm, dim} = this.props;
        const chartData = this.getChartData();
        const AED = this.getAED();
        return (
            <Panel className="panel-box">
                <h4 className="text-center">{'Summary Chart'}</h4>
                <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={chartData} margin={{top: 20, right: 30, left: 30, bottom: 5}}>
                        <XAxis dataKey="name" tickFormatter={this.formatXTiks}/>
                        <YAxis label={<CustomizedYLable lab={uOm}/>} interval="preserveStart" tickFormatter={this.formatYTiks}/>
                        <CartesianGrid strokeDasharray="3 3"/>
                        {this.getLines()}
                        <Legend verticalAlign="bottom" height={36}/>
                    </LineChart>
                </ResponsiveContainer>
                { AED.length > 0 ?
                <div>
                <h4 className="text-center">{'AED'}</h4>
                <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={AED} margin={{top: 20, right: 30, left: 30, bottom: 5}}>
                        <XAxis dataKey="name" tickFormatter={this.formatXTiks}/>
                        <YAxis label={<CustomizedYLable lab={uOm}/>} interval="preserveStart" tickFormatter={this.formatYTiks}/>
                        <CartesianGrid strokeDasharray="3 3"/>
                        <Bar type="monotone" dataKey={"value"}>
                        {
                            AED.map((entry, index) => {
                                const active = index === dim.dim1Idx;
                                return (<Cell strokeWidth={0} fill={active ? '#ff8f31' : '#333333'} key={`cell-${index}`}/>);
                            })
                        }
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
                </div> : null}
            </Panel>
        );
    },
    formatYTiks(v) {
        return v.toLocaleString();
    },
    formatXTiks(v) {
        return !isNaN(v) && parseFloat(v).toLocaleString() || v;
    }
});

module.exports = SummaryChart;
