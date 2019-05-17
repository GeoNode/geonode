 /**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactDOM = require('react-dom');
const ReactItem = require('../RecordItem.jsx');
const expect = require('expect');
const assign = require('object-assign');

const TestUtils = require('react-addons-test-utils');

const sampleRecord = {
    identifier: "test-identifier",
    title: "sample title",
    tags: ["subject1", "subject2"],
    description: "sample abstract",
    thumbnail: "img.jpg",
    boundingBox: {
        extent: [10.686,
                44.931,
                46.693,
                12.54],
        crs: "EPSG:4326"

    },
    references: [{
        type: "OGC:WMS",
        url: "http://wms.sample.service:80/geoserver/wms?SERVICE=WMS&",
        SRS: [],
        params: {name: "workspace:layername"}
    }]
};

const sampleRecord2 = {
    identifier: "test-identifier",
    title: "sample title",
    tags: ["subject1", "subject2"],
    description: "sample abstract",
    thumbnail: "img.jpg",
    boundingBox: {
        extent: [10.686,
                44.931,
                46.693,
                12.54],
        crs: "EPSG:4326"

    },
    references: [{
        type: "OGC:WMS",
        url: "http://wms.sample.service:80/geoserver/wms?SERVICE=WMS&",
        SRS: ['EPSG:4326'],
        params: {name: "workspace:layername"}
    }]
};

const sampleRecord3 = {
    identifier: "test-identifier",
    title: "sample title",
    tags: ["subject1", "subject2"],
    description: "sample abstract",
    thumbnail: "img.jpg",
    boundingBox: {
        extent: [10.686,
                44.931,
                46.693,
                12.54],
        crs: "EPSG:4326"

    },
    references: [{
        type: "OGC:WMTS",
        url: "http://wms.sample.service:80/geoserver/gwc/service/wmts",
        SRS: ['EPSG:4326', 'EPSG:3857'],
        params: {name: "workspace:layername"}
    }]
};

const getCapRecord = assign({}, sampleRecord, {references: [{
        type: "OGC:WMS",
        url: "http://wms.sample.service:80/geoserver/wms?SERVICE=WMS&",
        params: {name: "workspace:layername"}
    }, {
        type: "OGC:WMS-1.3.0-http-get-capabilities",
        url: "http://wms.sample.service:80/geoserver/workspace/layername/wms?service=wms&version=1.3.0&request=GetCapabilities&"
    }, {
        type: "OGC:WFS-1.0.0-http-get-capabilities",
        url: "http://wfs.sample.service:80/geoserver/workspace/layername/wfs?service=wfs&version=1.0.0&request=GetCapabilities"
    }
]});

describe('This test for RecordItem', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    // test DEFAULTS
    it('creates the component with defaults', () => {
        const item = ReactDOM.render(<ReactItem />, document.getElementById("container"));
        expect(item).toExist();

        const itemDom = ReactDOM.findDOMNode(item);
        expect(itemDom).toExist();

        expect(itemDom.className).toBe('record-item panel panel-default');
    });
    // test data
    it('creates the component with data', () => {
        const item = ReactDOM.render(<ReactItem record={sampleRecord}/>, document.getElementById("container"));
        expect(item).toExist();

        const itemDom = ReactDOM.findDOMNode(item);
        expect(itemDom).toExist();
        expect(itemDom.className).toBe('record-item panel panel-default');
    });
    it('check WMTS resource', () => {
        let actions = {
            onLayerAdd: () => {

            },
            onZoomToExtent: () => {

            }
        };
        let actionsSpy = expect.spyOn(actions, "onLayerAdd");
        let actionsSpy2 = expect.spyOn(actions, "onZoomToExtent");
        const item = ReactDOM.render((<ReactItem
            record={sampleRecord3}
            onLayerAdd={actions.onLayerAdd}
            onZoomToExtent={actions.onZoomToExtent}/>), document.getElementById("container"));
        expect(item).toExist();

        const itemDom = ReactDOM.findDOMNode(item);
        expect(itemDom).toExist();
        expect(itemDom.className).toBe('record-item panel panel-default');
        let button = TestUtils.findRenderedDOMComponentWithTag(
           item, 'button'
        );
        expect(button).toExist();
        button.click();
        expect(actionsSpy.calls.length).toBe(1);
        expect(actionsSpy2.calls.length).toBe(1);
    });
    // test handlers
    it('check event handlers', () => {
        let actions = {
            onLayerAdd: () => {

            },
            onZoomToExtent: () => {

            }
        };
        let actionsSpy = expect.spyOn(actions, "onLayerAdd");
        let actionsSpy2 = expect.spyOn(actions, "onZoomToExtent");
        const item = ReactDOM.render((<ReactItem
            record={sampleRecord}
            onLayerAdd={actions.onLayerAdd}
            onZoomToExtent={actions.onZoomToExtent}/>), document.getElementById("container"));
        expect(item).toExist();

        const itemDom = ReactDOM.findDOMNode(item);
        expect(itemDom).toExist();
        expect(itemDom.className).toBe('record-item panel panel-default');
        let button = TestUtils.findRenderedDOMComponentWithTag(
           item, 'button'
        );
        expect(button).toExist();
        button.click();
        expect(actionsSpy.calls.length).toBe(1);
        expect(actionsSpy2.calls.length).toBe(1);
    });

    it('test create record item with no get capabilities links', () => {
        // instanciating a record item component
        const component = ReactDOM.render(<ReactItem record={sampleRecord} showGetCapLinks={true}/>,
            document.getElementById("container"));
        // check that the component was intanciated
        expect(component).toExist();
        const componentDom = ReactDOM.findDOMNode(component);
        expect(componentDom).toExist();
        // we should have two buttons enable
        const buttons = componentDom.getElementsByTagName('button');
        expect(buttons.length).toBe(1);
    });

    it('test create record item with get capabilities links', () => {
        // instanciating a record item component
        const component = ReactDOM.render(<ReactItem record={getCapRecord} showGetCapLinks={true}/>,
            document.getElementById("container"));
        // check that the component was intanciated
        expect(component).toExist();
        const componentDom = ReactDOM.findDOMNode(component);
        expect(componentDom).toExist();
        // we should have two buttons enable
        const buttons = componentDom.getElementsByTagName('button');
        expect(buttons.length).toBe(2);
    });

    it('test create record item with get capabilities links but show get capabilities links disable', () => {
        // instanciating a record item component
        const component = ReactDOM.render(<ReactItem showGetCapLinks={false} record={getCapRecord} showGetCapLinks={false}/>,
            document.getElementById("container"));
        // check that the component was intanciated
        expect(component).toExist();
        const componentDom = ReactDOM.findDOMNode(component);
        expect(componentDom).toExist();
        // we should have only one button
        const buttons = componentDom.getElementsByTagName('button');
        expect(buttons.length).toBe(1);
    });

    // test handlers
    it('check add layer with unsupported crs', () => {
        let actions = {
            onError: () => {
            }
        };
        let actionsSpy = expect.spyOn(actions, "onError");
        const item = ReactDOM.render((<ReactItem
            record={sampleRecord2}
            onError={actions.onError}
            crs="EPSG:3857"/>), document.getElementById("container"));
        expect(item).toExist();

        let button = TestUtils.findRenderedDOMComponentWithTag(
           item, 'button'
        );
        expect(button).toExist();
        button.click();
        expect(actionsSpy.calls.length).toBe(1);
    });
    it('check add layer with bounding box', () => {
        let actions = {
            onLayerAdd: () => {

            },
            onZoomToExtent: () => {

            }
        };
        let actionsSpy = expect.spyOn(actions, "onLayerAdd");
        const item = ReactDOM.render((<ReactItem
            record={sampleRecord}
            onLayerAdd={actions.onLayerAdd}
            />), document.getElementById("container"));
        expect(item).toExist();

        const itemDom = ReactDOM.findDOMNode(item);
        expect(itemDom).toExist();
        expect(itemDom.className).toBe('record-item panel panel-default');
        let button = TestUtils.findRenderedDOMComponentWithTag(
           item, 'button'
        );
        expect(button).toExist();
        button.click();
        expect(actionsSpy.calls.length).toBe(1);
        expect(actionsSpy.calls[0].arguments[0].bbox).toExist();
        expect(actionsSpy.calls[0].arguments[0].bbox.crs).toExist();
        expect(actionsSpy.calls[0].arguments[0].bbox.bounds).toExist();
    });
});
