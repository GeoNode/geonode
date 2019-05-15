/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var Thumbnail = require('../Thumbnail.jsx');
var expect = require('expect');
const TestUtils = require('react-addons-test-utils');

describe('This test for Thumbnail', () => {


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
    it('creates the component with defaults, loading=true', () => {
        const thumbnailItem = ReactDOM.render(<Thumbnail loading={true}/>, document.getElementById("container"));
        expect(thumbnailItem).toExist();

        const thumbnailItemDom = ReactDOM.findDOMNode(thumbnailItem);
        expect(thumbnailItemDom).toExist();

        expect(thumbnailItemDom.className).toBe('btn btn-info');
    });

    it('creates the component with defaults, loading=false', () => {
        const thumbnailItem = ReactDOM.render(<Thumbnail loading={false}/>, document.getElementById("container"));
        expect(thumbnailItem).toExist();

        const thumbnailItemDom = ReactDOM.findDOMNode(thumbnailItem);
        expect(thumbnailItemDom).toExist();

        expect(thumbnailItemDom.className).toBe('dropzone-thumbnail-container');
    });

    it('creates the component without a thumbnail', () => {
        let thumbnail = "http://localhost:8081/%2Fgeostore%2Frest%2Fdata%2F2214%2Fraw%3Fdecode%3Ddatauri";
        let map = {
            thumbnail: thumbnail,
            id: 123,
            canWrite: true,
            errors: []
        };
        const thumbnailItem = ReactDOM.render(<Thumbnail map={map}/>, document.getElementById("container"));
        expect(thumbnailItem).toExist();

        const thumbnailItemDom = ReactDOM.findDOMNode(thumbnailItem);
        expect(thumbnailItemDom).toExist();

        const content = TestUtils.findRenderedDOMComponentWithClass(thumbnailItem, 'dropzone-content-image');
        expect(content).toExist();
    });

    it('creates the component with a thumbnail', () => {
        let thumbnail = "http://localhost:8081/%2Fgeostore%2Frest%2Fdata%2F2214%2Fraw%3Fdecode%3Ddatauri";
        let map = {
            thumbnail: thumbnail,
            newThumbnail: thumbnail,
            id: 123,
            canWrite: true,
            errors: []
        };
        const thumbnailItem = ReactDOM.render(<Thumbnail map={map}/>, document.getElementById("container"));
        expect(thumbnailItem).toExist();

        const thumbnailItemDom = ReactDOM.findDOMNode(thumbnailItem);
        expect(thumbnailItemDom).toExist();

        const content = TestUtils.findRenderedDOMComponentWithClass(thumbnailItem, 'dropzone-content-image-added');
        expect(content).toExist();
    });


    it('creates the component with a thumbnail, map=null, metadata=null', () => {
        let thumbnail = "http://localhost:8081/%2Fgeostore%2Frest%2Fdata%2F2214%2Fraw%3Fdecode%3Ddatauri";
        let map = {
            name: "nameMap",
            description: "descMap",
            thumbnail: thumbnail,
            newThumbnail: thumbnail,
            id: 123,
            canWrite: true,
            errors: []
        };

        const thumbnailItem = ReactDOM.render(<Thumbnail map={map}/>, document.getElementById("container"));
        expect(thumbnailItem).toExist();

        // map, metadata
        thumbnailItem.updateThumbnail(null, null);

        const thumbnailItemDom = ReactDOM.findDOMNode(thumbnailItem);
        expect(thumbnailItemDom).toExist();

        const content = TestUtils.findRenderedDOMComponentWithClass(thumbnailItem, 'dropzone-content-image-added');
        expect(content).toExist();
    });

    it('creates the component with a thumbnail, map=null, metadata=object', () => {
        let thumbnail = "http://localhost:8081/%2Fgeostore%2Frest%2Fdata%2F2214%2Fraw%3Fdecode%3Ddatauri";
        let map = {
            name: "nameMap",
            description: "descMap",
            thumbnail: thumbnail,
            newThumbnail: thumbnail,
            id: 123,
            canWrite: true,
            errors: []
        };

        let metadata = {
            name: "name of the map",
            description: "desc of the map"
        };

        const thumbnailItem = ReactDOM.render(<Thumbnail map={map}/>, document.getElementById("container"));
        expect(thumbnailItem).toExist();

        // map, metadata
        thumbnailItem.updateThumbnail(null, metadata);

        const thumbnailItemDom = ReactDOM.findDOMNode(thumbnailItem);
        expect(thumbnailItemDom).toExist();

        const content = TestUtils.findRenderedDOMComponentWithClass(thumbnailItem, 'dropzone-content-image-added');
        expect(content).toExist();
    });

    it('creates the component with a thumbnail, onDrop files=null', () => {
        let thumbnail = "http://localhost:8081/%2Fgeostore%2Frest%2Fdata%2F2214%2Fraw%3Fdecode%3Ddatauri";
        let map = {
            name: "nameMap",
            description: "descMap",
            thumbnail: thumbnail,
            newThumbnail: thumbnail,
            id: 123,
            canWrite: true,
            errors: []
        };

        const thumbnailItem = ReactDOM.render(<Thumbnail map={map}/>, document.getElementById("container"));
        expect(thumbnailItem).toExist();

        /*let files = [{
            type: "image/png",
            preview: "blob:http://dev.mapstore2.geo-solutions.it/6b67787f-0654-4107-94bf-165adf386259"
        }];*/

        // map, metadata
        thumbnailItem.onDrop(null);
        // thumbnailItem.onDrop(files);

        const thumbnailItemDom = ReactDOM.findDOMNode(thumbnailItem);
        expect(thumbnailItemDom).toExist();

        const content = TestUtils.findRenderedDOMComponentWithClass(thumbnailItem, 'dropzone-content-image-added');
        expect(content).toExist();
    });


    it('creates the component with a thumbnail, onRemoveThumbnail', () => {
        let thumbnail = "http://localhost:8081/%2Fgeostore%2Frest%2Fdata%2F2214%2Fraw%3Fdecode%3Ddatauri";
        let map = {
            name: "nameMap",
            description: "descMap",
            thumbnail: thumbnail,
            newThumbnail: thumbnail,
            id: 123,
            canWrite: true,
            errors: []
        };

        const thumbnailItem = ReactDOM.render(<Thumbnail map={map}/>, document.getElementById("container"));
        expect(thumbnailItem).toExist();

        // map, metadata
        thumbnailItem.onRemoveThumbnail(null);

        const thumbnailItemDom = ReactDOM.findDOMNode(thumbnailItem);
        expect(thumbnailItemDom).toExist();

        const content = TestUtils.findRenderedDOMComponentWithClass(thumbnailItem, 'dropzone-content-image-added');
        expect(content).toExist();
    });

    it('creates the component with a thumbnail, deleteThumbnail(thumbnail, mapId)', () => {
        let thumbnail = "http://localhost:8081/%2Fgeostore%2Frest%2Fdata%2F2214%2Fraw%3Fdecode%3Ddatauri";
        let map = {
            name: "nameMap",
            description: "descMap",
            thumbnail: thumbnail,
            newThumbnail: thumbnail,
            id: 123,
            canWrite: true,
            errors: []
        };

        const thumbnailItem = ReactDOM.render(<Thumbnail map={map}/>, document.getElementById("container"));
        expect(thumbnailItem).toExist();

        // map, metadata
        thumbnailItem.deleteThumbnail(thumbnail, map.id);

        const thumbnailItemDom = ReactDOM.findDOMNode(thumbnailItem);
        expect(thumbnailItemDom).toExist();

        const content = TestUtils.findRenderedDOMComponentWithClass(thumbnailItem, 'dropzone-content-image-added');
        expect(content).toExist();
    });
});
