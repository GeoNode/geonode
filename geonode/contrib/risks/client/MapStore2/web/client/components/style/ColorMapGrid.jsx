/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {isEqual} = require('lodash');
const {AgGridReact} = require('ag-grid-react');
const reactCellRendererFactory = require('./ColorMapGridComponents/ReactCellRendererFactoryParams');
const ColorPickerRenderer = require('./ColorMapGridComponents/ColorPickerRenderer');
const assign = require('object-assign');
const NumberRenderer = require('./ColorMapGridComponents/NumberRenderer');

const LocaleUtils = require('../../utils/LocaleUtils');

require("ag-grid/dist/styles/ag-grid.css");
require("ag-grid/dist/styles/theme-blue.css");

const ColorMapGrid = React.createClass({
    propTypes: {
        entries: React.PropTypes.array,
        style: React.PropTypes.object,
        selectEntry: React.PropTypes.func,
        valueChanged: React.PropTypes.func
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            entries: [],
            style: {height: "200px"},
            selectEntry: () => {},
            valueChanged: () => {}
        };
    },
    shouldComponentUpdate(nextProps) {
        return !isEqual(nextProps.entries, this.props.entries);
    },
    componentDidUpdate() {
        this.api.sizeColumnsToFit();
    },
    onGridReady(params) {
        this.api = params.api;
        this.api.sizeColumnsToFit();
        this.columnApi = params.columnApi;
    },
    render() {
        return (
            <div fluid={true} style={this.props.style} className="ag-blue">
                <AgGridReact
                    columnDefs={[{
                        width: 50,
                        suppressSizeToFit: true,
                        headerName: LocaleUtils.getMessageById(this.context.messages, "colormapgrid.color"),
                        field: "color",
                        cellRenderer: reactCellRendererFactory(ColorPickerRenderer, { onChangeColor: this.changeColor})

                    }, {
                        width: 135,
                        headerName: LocaleUtils.getMessageById(this.context.messages, "colormapgrid.quantity"),
                        field: "quantity",
                        cellRenderer: reactCellRendererFactory(NumberRenderer, { onChangeValue: this.changeQuantity, errorMessage: LocaleUtils.getMessageById(this.context.messages, "colormapgrid.minmaxerror")})
                    }, {
                        width: 160,
                        headerName: LocaleUtils.getMessageById(this.context.messages, "colormapgrid.label"),
                        field: "label",
                        editable: true
                    }]}
                    rowHeight={32}
                    rowData={this.props.entries.slice()}
                    rowSelection="single"
                    onRowSelected={this.selectEntry}
                    onCellValueChanged={this.valueChanged}
                    enableColResize={true}
                    showToolPanel={false}
                    rowDeselection={true}
                    onGridReady={this.onGridReady}
                    suppressCellSelection={true}
                />
            </div>);
    },
    selectEntry(row) {
        if (row) {
            this.props.selectEntry(row.node.childIndex);
        }
    },
    valueChanged() {
        let newData = [];
        this.api.getModel().forEachNode((node) => {newData.push(node.data); });
        this.props.valueChanged(newData);
    },
    changeColor(node, colorOpacity) {
        let newData = [];
        this.api.getModel().forEachNode((n, idx) => {
            let data = (idx === node.childIndex) ? assign({}, n.data, colorOpacity) : n.data;
            newData.push(data);
        });
        this.props.valueChanged(newData);
    },
    changeQuantity(node, value) {
        let newData = [];
        this.api.getModel().forEachNode((n, idx) => {
            let data = (idx === node.childIndex) ? assign({}, n.data, {quantity: value}) : n.data;
            newData.push(data);
        });
        this.props.valueChanged(newData);
    }
});

module.exports = ColorMapGrid;
