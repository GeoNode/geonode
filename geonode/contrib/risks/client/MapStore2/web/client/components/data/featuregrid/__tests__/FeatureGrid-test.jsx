/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require("react");
const expect = require('expect');
const ReactDOM = require('react-dom');
const FeatureGrid = require('../FeatureGrid');
const data = require("json-loader!../../../../test-resources/featureGrid-test-data.json");

const columnDef = [
    {headerName: "Name", field: "properties.NAME_STATE", width: 150, pinned: true}
];

describe("Test FeatureGrid Component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('Test FeatureGrid rendering', () => {
        let comp = ReactDOM.render(
            <FeatureGrid features={data.features}/>, document.getElementById("container"));
        expect(comp).toExist();
        let btns = document.getElementsByTagName("button");
        btns[btns.length - 1].click();
        // comp.setProps({paging: true, features: function() { return data.features; }, columnDefs: columnDef});
    });
    it('Test FeatureGrid rendering with column def', () => {
        let comp = ReactDOM.render(
            <FeatureGrid features={data.features} columnDefs={columnDef} virtualPaging={true}/>, document.getElementById("container"));
        expect(comp).toExist();
    });
    it('Test FeatureGrid rendering without column defs', () => {
        let map = {
            size: {width: 1360, height: 685},
            center: {x: -98, y: 26, crs: "EPSG:4326"},
            projection: "EPSG:900913"
        };
        let comp = ReactDOM.render(
            <FeatureGrid features={data.features} paging={true} map={map}/>, document.getElementById("container"));
        comp.getRows({sortModel: [{colId: "properties.STATE_NAME", sort: 'asc'}], startRow: 0, endRow: 100, successCallback: () => {}});
        comp.getRows({sortModel: [{colId: "properties.STATE_NAME", sort: 'desc'}], startRow: 0, endRow: 100, successCallback: () => {}});
        let params = {data: {geometry: {}}};
        comp.zoomToFeature(params);
        comp.zoomToFeatures();
        params = {selectedRows: []};
        comp.selectFeatures(params);
        expect(comp).toExist();
    });
    it('Test FeatureGrid custom zoomToFeatures', () => {
        let map = {
            size: {width: 1360, height: 685},
            center: {x: -98, y: 26, crs: "EPSG:4326"},
            projection: "EPSG:900913"
        };
        const testZoomTo = {
            action: () => {
                return true;
            }
        };
        const spy = expect.spyOn(testZoomTo, 'action');

        let comp = ReactDOM.render(
            <FeatureGrid features={data.features} paging={true} map={map} zoomToFeatureAction={testZoomTo.action}/>, document.getElementById("container"));
        expect(comp).toExist();
        let params = {data: {geometry: {coordinates: []}}};
        comp.zoomToFeature(params);
        expect(spy).toHaveBeenCalled();
        expect(spy).toHaveBeenCalledWith(params.data);
    });
});
