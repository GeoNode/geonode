/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {AgGridReact, reactCellRendererFactory} = require('ag-grid-react');
const {keys, isEqual, isFunction} = require('lodash');
const ZoomToFeatureIcon = require("./ZoomToFeatureIcon");
const ZoomToFeatureRenderer = require('./ZoomToFeatureRenderer');
const {ButtonToolbar, Button, Glyphicon} = require('react-bootstrap');
const assign = require("object-assign");

const mapUtils = require('../../../utils/MapUtils');
const configUtils = require('../../../utils/ConfigUtils');
const CoordinateUtils = require('../../../utils/CoordinatesUtils');

const I18N = require('../../I18N/I18N');
const LocaleUtils = require('../../../utils/LocaleUtils');

require("ag-grid/dist/styles/ag-grid.css");
require("ag-grid/dist/styles/theme-fresh.css");

const FeatureGrid = React.createClass({
    propTypes: {
        features: React.PropTypes.oneOfType([React.PropTypes.array, React.PropTypes.func]),
        select: React.PropTypes.array,
        columnDefs: React.PropTypes.array,
        changeMapView: React.PropTypes.func,
        selectFeatures: React.PropTypes.func,
        highlightedFeatures: React.PropTypes.array,
        style: React.PropTypes.object,
        virtualPaging: React.PropTypes.bool,
        paging: React.PropTypes.bool,
        pageSize: React.PropTypes.number,
        overflowSize: React.PropTypes.number,
        agGridOptions: React.PropTypes.object,
        columnDefaultOptions: React.PropTypes.object,
        excludeFields: React.PropTypes.array,
        map: React.PropTypes.object,
        enableZoomToFeature: React.PropTypes.bool,
        srs: React.PropTypes.string,
        maxZoom: React.PropTypes.number,
        zoom: React.PropTypes.number,
        toolbar: React.PropTypes.object,
        dataSource: React.PropTypes.object,
        selectAll: React.PropTypes.func,
        selectAllActive: React.PropTypes.bool,
        zoomToFeatureAction: React.PropTypes.func,
        exportAction: React.PropTypes.func,
        tools: React.PropTypes.array,
        useIcons: React.PropTypes.bool
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            highlightedFeatures: null,
            features: null,
            select: [],
            columnDefs: null,
            changeMapView: () => {},
            selectFeatures: () => {},
            style: {
                height: "400px",
                width: "800px"
            },
            virtualPaging: false,
            paging: false,
            overflowSize: 10,
            pageSize: 10,
            agGridOptions: {},
            columnDefaultOptions: {
                width: 125
            },
            excludeFields: [],
            map: {},
            zoom: null,
            enableZoomToFeature: true,
            srs: "EPSG:4326",
            tools: [],
            toolbar: {
                zoom: true,
                exporter: true,
                toolPanel: true,
                selectAll: true
            },
            dataSource: null,
            selectAllActive: false,
            exportAction: (api) => {
                if ( api) {
                    api.exportDataAsCsv();
                }
            }
        };
    },
    shouldComponentUpdate(nextProps) {
        return !isEqual(nextProps, this.props);
    },
    componentWillUpdate(nextProps) {
        if (!isEqual(nextProps.features, this.props.features) && (this.api.getSelectedNodes().length > 0)) {
            this.suppresSelectionEvent = true;
        }
    },
    componentDidUpdate() {
        if (this.props.highlightedFeatures) {
            this.selectHighlighted();
        }
    },
    onGridReady(params) {
        this.api = params.api;
        this.columnApi = params.columnApi;
        if (this.props.highlightedFeatures) {
            this.selectHighlighted();
        }
    },
    // Internal function that simulate data source getRows for in memory data
    getRows(params) {
        let data = this.props.features;
        if (params.sortModel && params.sortModel.length > 0) {
            data = this.sortData(params.sortModel, data);
        }
        let rowsThisPage = data.slice(params.startRow, params.endRow);
        let lastRow = -1;
        if (data.length <= params.endRow) {
            lastRow = data.length;
        }
        params.successCallback(rowsThisPage, lastRow);
    },
    render() {
        let isPagingOrVirtual = (this.props.virtualPaging || this.props.paging);

        let tools = [];
        if (this.props.toolbar.zoom) {
            tools.push(<Button key="zoom" onClick={this.zoomToFeatures}><Glyphicon glyph="search"/></Button>);
        }

        if (this.props.toolbar.exporter) {
            tools.push(<Button key="exporter" onClick={() => this.props.exportAction(this.api)}>
                <Glyphicon glyph="download"/><I18N.Message msgId={"featuregrid.export"}/>
            </Button>);
        }

        if (this.props.toolbar.toolPanel) {
            tools.push(<Button key="toolPanel" onClick={() => { this.api.showToolPanel(!this.api.isToolPanelShowing()); }}>
                <Glyphicon glyph="cog"/><I18N.Message msgId={"featuregrid.tools"}/>
            </Button>);
        }

        if (this.props.toolbar.selectAll) {
            let nOfFeatures = this.props.features && this.props.features.length;
            if (this.props.paging && this.api) {
                nOfFeatures = 0;
                this.api.forEachNode(() => {nOfFeatures++; });
            }
            let allSelected = false;
            if (this.props.selectAll) {
                allSelected = this.props.selectAllActive;
            }else {
                allSelected = !(this.props.select.length < nOfFeatures);
            }
            tools.push(<Button key="allrowsselection" onClick={() => {
                if (this.props.selectAll) {
                    if (!allSelected && this.api) {
                        this.api.deselectAll();
                    }
                    this.props.selectAll(!allSelected);
                } else {
                    this.selectAllRows(!allSelected);
                }
            }}><Glyphicon glyph="check"/>
                {
                    (!allSelected) ? (
                        <I18N.Message msgId={"featuregrid.selectall"}/>
                    ) : (
                        <I18N.Message msgId={"featuregrid.deselectall"}/>
                    )
                }
            </Button>);
        }
        tools = [...tools, this.props.tools];
        return (
            <div style={{
                display: "flex",
                flexDirection: "column",
                height: "100%"
            }}>
                <div fluid={false} style={this.props.style} className="ag-fresh">
                    <AgGridReact
                        virtualPaging={this.props.virtualPaging}
                        columnDefs={this.setColumnDefs()}
                        rowData={(!isPagingOrVirtual) ? this.props.features : null}
                        datasource={(isPagingOrVirtual) ? this.setDataSource() : null}
                        enableServerSideSorting={(isPagingOrVirtual)}
                        // or provide props the old way with no binding
                        onSelectionChanged={this.selectFeatures}
                        rowSelection="multiple"
                        enableColResize={true}
                        enableSorting={(!isPagingOrVirtual)}
                        toolPanelSuppressValues={true}
                        toolPanelSuppressGroups={true}
                        showToolPanel={false}
                        rowDeselection={true}
                        localeText={{
                            page: LocaleUtils.getMessageById(this.context.messages, "featuregrid.pagination.page") || 'Page',
                            of: LocaleUtils.getMessageById(this.context.messages, "featuregrid.pagination.of") || 'of',
                            to: LocaleUtils.getMessageById(this.context.messages, "featuregrid.pagination.to") || 'to',
                            more: LocaleUtils.getMessageById(this.context.messages, "featuregrid.pagination.more") || 'more',
                            next: '>',
                            last: '>|',
                            first: '|<',
                            previous: '<'}}
                        onGridReady={this.onGridReady}
                        {...this.props.agGridOptions}
                    />
                </div>
                <ButtonToolbar className="featuregrid-tools" style={{marginTop: "5px", marginLeft: "0px", flex: "none"}} bsSize="sm">
                    {tools.map((tool) => tool)}
                </ButtonToolbar>
            </div>);
    },
    // If props.columnDefs is missing try to generate from features, add zoomTo as first column
    setColumnDefs() {
        let defs = this.props.columnDefs;
        let defaultOptions = this.props.columnDefaultOptions;
        let exclude = this.props.excludeFields;
        if (!defs && this.props.features && this.props.features[0]) {
            defs = keys(this.props.features[0].properties).filter((val) => {
                return exclude.indexOf(val) === -1;
            }).map(function(key) {
                return assign({}, defaultOptions, {headerName: key, field: "properties." + key});
            });
        }
        return (this.props.enableZoomToFeature) ? [
        {
            onCellClicked: this.zoomToFeature,
            headerName: '',
            cellRenderer: reactCellRendererFactory(this.props.useIcons ? ZoomToFeatureIcon : ZoomToFeatureRenderer),
            suppressSorting: true,
            suppressMenu: true,
            pinned: true,
            width: 25,
            suppressResize: true
        }].concat(defs) : defs;

    },
    // Generate datasource for pagination or virtual paging and infinite scrolling
    setDataSource() {
        return (this.props.dataSource) ? this.props.dataSource : {
            rowCount: (isFunction(this.props.features)) ? -1 : this.props.features.length,
            getRows: (isFunction(this.props.features)) ? this.props.features : this.getRows,
            pageSize: this.props.pageSize,
            overflowSize: this.props.overflowSize
        };
    },
    zoomToFeature(params) {
        let geometry = params.data.geometry;
        if (geometry.coordinates) {

            if (this.props.zoomToFeatureAction) {
                this.props.zoomToFeatureAction(params.data);
            } else {
                this.changeMapView([geometry], this.props.zoom);
            }
        }
    },
    zoomToFeatures() {
        let geometries = [];

        let getGeoms = function(nodes) {
            let geom = [];
            nodes.forEach(function(node) {
                if (node.group) {
                    geom = geom.concat(getGeoms(node.children));
                } else {
                    geom.push(node.data.geometry);
                }
            });
            return geom;
        };

        let model = this.api.getModel();
        model.forEachNode(function(node) {
            if (node.group) {
                geometries = geometries.concat(getGeoms(node.children));
            }else {
                geometries.push(node.data.geometry);
            }
        });

        geometries = geometries.filter((geometry) => geometry.coordinates);

        if (geometries.length > 0) {
            this.changeMapView(geometries);
        }
    },
    changeMapView(geometries, zoom) {
        let extent = geometries.reduce((prev, next) => {
            return CoordinateUtils.extendExtent(prev, CoordinateUtils.getGeoJSONExtent(next));
        }, CoordinateUtils.getGeoJSONExtent(geometries[0]));

        const mapSize = this.props.map.size;
        let newZoom = 1;
        let newCenter = this.props.map.center;
        const proj = this.props.map.projection || "EPSG:3857";

        if (extent) {
            extent = (this.props.srs !== proj) ? CoordinateUtils.reprojectBbox(extent, this.props.srs, proj) : extent;
            // zoom by the max. extent defined in the map's config
            newZoom = zoom ? zoom : mapUtils.getZoomForExtent(extent, mapSize, 0, 21);
            newZoom = (this.props.maxZoom && newZoom > this.props.maxZoom) ? this.props.maxZoom : newZoom;

            // center by the max. extent defined in the map's config
            newCenter = mapUtils.getCenterForExtent(extent, proj);

            // do not reproject for 0/0
            if (newCenter.x !== 0 || newCenter.y !== 0) {
                // reprojects the center object
                newCenter = configUtils.getCenter(newCenter, "EPSG:4326");
            }
            // adapt the map view by calling the corresponding action
            this.props.changeMapView(newCenter, newZoom,
                this.props.map.bbox, this.props.map.size, null, proj);
        }
    },
    selectAllRows(select) {
        // this.props.selectFeatures(this.props.features.slice());
        if (select === true) {
            this.api.selectAll();
        } else {
            this.api.deselectAll();
        }
    },
    selectFeatures(params) {
        if (!this.suppresSelectionEvent) {
            this.props.selectFeatures(params.selectedRows.slice());
        }else {
            this.suppresSelectionEvent = false;
        }
    },
    sortData(sortModel, data) {
        // do an in memory sort of the data, across all the fields
        let resultOfSort = data.slice();
        resultOfSort.sort(function(a, b) {
            for (let k = 0; k < sortModel.length; k++) {
                let sortColModel = sortModel[k];
                let colId = sortColModel.colId.split(".");
                /*eslint-disable */
                let valueA = colId.reduce(function(d, key) {
                    return (d) ? d[key] : null;
                }, a);
                let valueB = colId.reduce(function(d, key) {
                    return (d) ? d[key] : null;
                }, b);
                /*eslint-enable */
                // this filter didn't find a difference, move onto the next one
                if (valueA === valueB) {
                    continue;
                }
                let sortDirection = sortColModel.sort === 'asc' ? 1 : -1;
                return (valueA > valueB) ? sortDirection : sortDirection * -1;

            }
            // no filters found a difference
            return 0;
        });
        return resultOfSort;
    },
    // If highlighted features are passed we try to select corresponding row
    // using geojson feature id
    selectHighlighted() {
        let selectedId = this.props.highlightedFeatures;
        let me = this;
        this.api.forEachNode((n) => {
            if (selectedId.indexOf(n.data.id) !== -1) {
                me.api.selectNode(n, true, true);
            }else if (me.api.isNodeSelected(n)) {
                me.suppresSelectionEvent = true;
                me.api.deselectNode(n);
            }
        });
    }
});

module.exports = FeatureGrid;
