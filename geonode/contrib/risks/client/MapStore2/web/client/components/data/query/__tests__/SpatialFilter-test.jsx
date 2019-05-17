/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactDOM = require('react-dom');

const SpatialFilter = require('../SpatialFilter.jsx');

const {featureCollection} = require('../../../../test-resources/featureCollectionZone.js');

const expect = require('expect');

describe('SpatialFilter', () => {

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates the SpatialFilter component', () => {
        let spatialField = {
            method: null,
            attribute: "the_geom",
            operation: "INTERSECTS",
            geometry: null
        };

        const spatialfilter = ReactDOM.render(
            <SpatialFilter
                spatialField={spatialField}
                spatialPanelExpanded={true}
                showDetailsPanel={false}/>,
            document.getElementById("container")
        );

        expect(spatialfilter).toExist();
        expect(spatialfilter.props.spatialField).toExist();
        expect(spatialfilter.props.spatialField).toBe(spatialField);
        expect(spatialfilter.props.spatialPanelExpanded).toBe(true);
        expect(spatialfilter.props.showDetailsPanel).toBe(false);

        const spatialFilterDOMNode = expect(ReactDOM.findDOMNode(spatialfilter));
        expect(spatialFilterDOMNode).toExist();

        let spatialPanel = spatialFilterDOMNode.actual.childNodes[0].childNodes[1].id;
        expect(spatialPanel).toExist();
        expect(spatialPanel).toBe("spatialFilterPanel");

        let combosPanel = spatialFilterDOMNode.actual.getElementsByClassName('panel-body');
        expect(combosPanel).toExist();

        let containerFluid = combosPanel[1].childNodes[0];
        expect(containerFluid).toExist();
        expect(containerFluid.className).toBe("container-fluid");

        let logicHeader = containerFluid.childNodes[0];
        expect(logicHeader).toExist();
        expect(logicHeader.className).toBe("logicHeader filter-field-row row");

        let operationPanelRows = combosPanel[2].getElementsByClassName('row');
        expect(operationPanelRows.length).toBe(2);
    });

    it('creates the SpatialFilter with the ZoneField component', () => {
        let spatialField = {
            method: "ZONE",
            attribute: "the_geom",
            operation: "INTERSECTS",
            geometry: null,
            zoneFields: [{
                id: 1,
                url: null,
                typeName: "geosolutions:zones",
                values: featureCollection.features,
                value: null,
                valueField: "properties.ITD_Dist_n",
                textField: "properties.DistNum",
                searchText: "*",
                searchMethod: "ilike",
                searchAttribute: "DistNum",
                label: "Zones"
            }, {
                id: 2,
                url: null,
                typeName: "geosolutions:county",
                label: "County",
                values: [],
                value: null,
                valueField: "properties.juris_code",
                textField: "properties.name2",
                searchText: "*",
                searchMethod: "ilike",
                searchAttribute: "name2",
                disabled: true,
                dependson: {
                    id: 1,
                    field: "itd_dist",
                    value: null
                }
            }]
        };

        const spatialfilter = ReactDOM.render(
            <SpatialFilter
                spatialField={spatialField}
                spatialPanelExpanded={false}
                showDetailsPanel={false}
                spatialMethodOptions={[
                    {id: "ZONE", name: "queryform.spatialfilter.methods.zone"}
                ]}
                spatialOperations={[
                    {id: "INTERSECTS", name: "queryform.spatialfilter.operations.intersects"}
                ]}/>,
            document.getElementById("container")
        );

        expect(spatialfilter).toExist();
        expect(spatialfilter.props.spatialField).toExist();
        expect(spatialfilter.props.spatialField).toBe(spatialField);
        expect(spatialfilter.props.spatialPanelExpanded).toBe(false);
        expect(spatialfilter.props.showDetailsPanel).toBe(false);

        const spatialFilterDOMNode = expect(ReactDOM.findDOMNode(spatialfilter));
        expect(spatialFilterDOMNode).toExist();

        let combosPanels = spatialFilterDOMNode.actual.getElementsByClassName('zone-combo');
        expect(combosPanels).toExist();
        expect(combosPanels.length).toBe(2);
    });
});
