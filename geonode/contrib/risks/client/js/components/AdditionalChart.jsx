/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Cell, BarChart, Tooltip, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer} = require('recharts');
const {Panel} = require('react-bootstrap');
const ChartTooltip = require("./ChartTooltip");

const CustomizedYLabel = (props) => {
    const {y, lab, viewBox} = props;
    return (
        <g>
            <text x={viewBox.width / 2} y={y} dy={-25} dx={0} textAnchor="middle" fill="#333" transform="rotate(0)">{lab}</text>
        </g>
    );
};

const CustomizedXLabel = (props) => {
    const {x, y, payload} = props;
    let val = payload.value.split(" ")[0];
    val = val.length > 8 ? val.substring(0, 8) + '...' : val;
    return (
      <g transform={`translate(${x},${y})`}>
          <text x={0} y={0} dx={-4} textAnchor="end" fill="#333" transform="rotate(-90)">{val}</text>
      </g>
    );
};

const AdditionalChart = React.createClass({
    propTypes: {
        tables: React.PropTypes.array,
        currentTable: React.PropTypes.number,
        currentSection: React.PropTypes.number,
        currentCol: React.PropTypes.number,
        setIndex: React.PropTypes.func,
        dim: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            tables: [],
            currentTable: 0,
            currentSection: 0,
            currentCol: 0,
            setIndex: () => {},
            dim: {}
        };
    },
    getChartData(values, scenarios) {
        return values[this.props.currentCol].map((v, idx) => {return {value: parseFloat(v, 10), name: scenarios[idx].label}; });
    },
    getTableData(values, scenarios) {
        return values[this.props.currentCol].map((v, idx) => {return {value: v, name: scenarios[idx].label}; });
    },
    renderSwitchBar(cols, sections, tables) {
        return (
            <div>
                <ul className="nav nav-pills">
                    <div className="text-center" style={{marginBottom: 20}}>{'Tables'}</div>
                    {
                        tables.map((val, idx) => {
                            let active = idx === this.props.currentTable ? 'active' : '';
                            return (<li key={idx} className={active} onClick={() => { this.props.setIndex(0, 0, idx); }}><a onClick={(e) => { e.preventDefault(); }} href="#">{val.name}</a></li>);
                        })
                    }
                </ul>
                <hr/>
                <div className="text-center" style={{marginBottom: 20}}>{'Sections'}</div>
                <ul className="nav nav-pills">
                {
                    sections.map((val, idx) => {
                        let active = idx === this.props.currentSection ? 'active' : '';
                        return <li key={idx} className={active} onClick={() => { this.props.setIndex(idx, 0, this.props.currentTable); }}><a onClick={(e) => { e.preventDefault(); }} href="#">{val.title}</a></li>;
                    })
                }
                </ul>
                <hr/>
                <ul className="nav nav-pills">
                <div className="text-center" style={{marginBottom: 20}}>{'Columns'}</div>
                {
                    cols.map((val, idx) => {
                        let active = idx === this.props.currentCol ? 'active' : '';
                        return (<li key={idx} className={active} onClick={() => { this.props.setIndex(this.props.currentSection, idx, this.props.currentTable); }}><a onClick={(e) => { e.preventDefault(); }} href="#">{val.label}</a></li>);
                    })
                }
                </ul>
            </div>
        );
    },
    renderTable(values, scenarios) {
        const tableData = this.getTableData(values, scenarios);
        return (
            <div className="container-fluid">
                <table className="table table-bordered">
                    <tbody>
                    {
                        tableData.map((v, idx) => {
                            let color = idx === this.props.dim.dim1Idx ? '#6646c2' : '#333';
                            color = idx === 0 ? '#ff8f31' : color;
                            return (
                                <tr key={idx}>
                                    <td style={{color}}>{v.name}</td>
                                    <td style={{color}}>{v.value}</td>
                                </tr>
                            );
                        })
                    }
                    </tbody>
                </table>
            </div>
        );
    },
    renderChart(values, scenarios, cols) {
        const chartData = this.getChartData(values, scenarios);
        return (
            <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData} onClick={this.handleClick} margin={{top: 50, right: 30, left: 30, bottom: 50}}>
                    <Bar type="monotone" dataKey="value" fill="#333" >
                    {
                        chartData.map((entry, index) => {
                            let color = index === this.props.dim.dim1Idx ? '#6646c2' : '#333';
                            color = index === 0 ? '#ff8f31' : color;
                            return (<Cell strokeWidth={1} stroke={color} fill={color} key={`cell-${index}`}/>);
                        })
                    }
                    </Bar>
                    <CartesianGrid horizontal={false} strokeDasharray="3 3"/>
                    <Tooltip content={<ChartTooltip xAxisLabel={'Scenario'} xAxisUnit={''} uOm={cols[this.props.currentCol].uOfm}/>}/>
                    <XAxis tick={<CustomizedXLabel/>} interval={0} dataKey="name" tickFormatter={this.formatXTiks}/>
                    <YAxis label={<CustomizedYLabel lab={cols[this.props.currentCol].uOfm}/>} interval="preserveStart" tickFormatter={this.formatYTiks}/>
                </BarChart>
            </ResponsiveContainer>
        );
    },
    renderCharts(tables) {
        const {sections = [], scenarios} = tables[this.props.currentTable].table;
        const {title, values, cols} = sections[this.props.currentSection];
        const display = this.checkNaN(values[this.props.currentCol]).length > 0 ? this.renderTable(values, scenarios, cols) : this.renderChart(values, scenarios, cols);
        return (
            <Panel className="panel-box">
                <h4 className="text-center">{title}</h4>
                <div className="text-center">{cols[this.props.currentCol].label}</div>
                {display}
                {this.renderSwitchBar(cols, sections, tables)}
            </Panel>
        );
    },
    getTables() {
        return this.props.tables.filter((val) => {
            return val && val.table && val.table.sections && val.table.sections.length > 0;
        });
    },
    render() {
        const tables = this.getTables();
        return tables.length > 0 && tables[this.props.currentTable] ? this.renderCharts(tables) : null;
    },
    formatYTiks(v) {
        return v.toLocaleString();
    },
    formatXTiks(v) {
        return !isNaN(v) && parseFloat(v).toLocaleString() || v;
    },
    checkNaN(values) {
        return values.filter((v) => {
            return isNaN(v);
        });
    }
});

module.exports = AdditionalChart;
