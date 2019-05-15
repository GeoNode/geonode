/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactDOM = require('react-dom');

const GeometryDetails = require('../GeometryDetails.jsx');

const expect = require('expect');

describe('GeometryDetails', () => {

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates the GeometryDetails component with Circle selection', () => {
        let geometry = {
            center: {
                srs: "EPSG:900913",
                x: -1761074.344349588,
                y: 5852757.632510748
            },
            projection: "EPSG:900913",
            radius: 836584.05,
            type: "Polygon"
        };

        let type = "Circle";

        const geometryDetails = ReactDOM.render(
            <GeometryDetails
                geometry={geometry}
                type={type}/>,
            document.getElementById("container")
        );

        expect(geometryDetails).toExist();
        expect(geometryDetails.props.geometry).toExist();
        expect(geometryDetails.props.geometry).toBe(geometry);
        expect(geometryDetails.props.type).toExist(true);
        expect(geometryDetails.props.type).toBe("Circle");

        const geometryDetailsDOMNode = expect(ReactDOM.findDOMNode(geometryDetails));
        expect(geometryDetailsDOMNode).toExist();

        let childNodes = geometryDetailsDOMNode.actual.childNodes;
        expect(childNodes.length).toBe(1);
        expect(childNodes[0].className).toBe("panel-body");

        let panelBodyRows = childNodes[0].getElementsByClassName('row');
        expect(panelBodyRows).toExist();
        expect(panelBodyRows.length).toBe(4);

        expect(panelBodyRows[0].childNodes.length).toBe(4);
    });

    it('creates the GeometryDetails component with BBOX selection', () => {
        let geometry = {
            extent: [
                -1335833.8895192828,
                5212046.6457833825,
                -543239.115071175,
                5785158.045300978
            ],
            projection: "EPSG:900913",
            type: "Polygon"
        };

        let type = "BBOX";

        const geometryDetails = ReactDOM.render(
            <GeometryDetails
                geometry={geometry}
                type={type}/>,
            document.getElementById("container")
        );

        expect(geometryDetails).toExist();
        expect(geometryDetails.props.geometry).toExist();
        expect(geometryDetails.props.geometry).toBe(geometry);
        expect(geometryDetails.props.type).toExist(true);
        expect(geometryDetails.props.type).toBe("BBOX");

        const geometryDetailsDOMNode = expect(ReactDOM.findDOMNode(geometryDetails));
        expect(geometryDetailsDOMNode).toExist();

        let childNodes = geometryDetailsDOMNode.actual.childNodes;
        expect(childNodes.length).toBe(1);
        expect(childNodes[0].className).toBe("panel-body");

        let panelBodyRows = childNodes[0].getElementsByClassName('row');
        expect(panelBodyRows).toExist();
        expect(panelBodyRows.length).toBe(4);
    });
});
