/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var MetadataModal = require('../MetadataModal.jsx');
var expect = require('expect');

describe('This test for MetadataModal', () => {


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
    it('creates the component with defaults, show=false', () => {
        const metadataModalItem = ReactDOM.render(<MetadataModal show={false}/>, document.getElementById("container"));
        expect(metadataModalItem).toExist();

        const metadataModalItemDom = ReactDOM.findDOMNode(metadataModalItem);
        expect(metadataModalItemDom).toExist();

        const getModals = function() {
            return document.getElementsByTagName("body")[0].getElementsByClassName('modal-dialog');
        };
        expect(getModals().length).toBe(0);

    });

    it('creates the component with defaults, show=true', () => {
        let thumbnail = "myThumnbnailUrl";
        let errors = ["FORMAT"];
        let map = {
            thumbnail: thumbnail,
            id: 123,
            canWrite: true,
            errors: errors
        };

        const metadataModalItem = ReactDOM.render(<MetadataModal show={true} useModal={true} map={map} id="MetadataModal"/>, document.getElementById("container"));
        expect(metadataModalItem).toExist();

        const modalDivList = document.getElementsByClassName("modal-content");
        const closeBtnList = modalDivList.item(0).getElementsByTagName('button');
        expect(closeBtnList.length).toBe(3);
    });

    it('creates the component with a format error', () => {
        let thumbnail = "myThumnbnailUrl";
        let errors = ["FORMAT"];
        let map = {
            thumbnail: thumbnail,
            id: 123,
            canWrite: true,
            errors: errors
        };

        const metadataModalItem = ReactDOM.render(<MetadataModal show={true} map={map} useModal={true} id="MetadataModal"/>, document.getElementById("container"));
        expect(metadataModalItem).toExist();

        const getModals = function() {
            return document.getElementsByTagName("body")[0].getElementsByClassName('modal-dialog');
        };

        expect(getModals().length).toBe(1);

        const modalDivList = document.getElementsByClassName("modal-content");
        const closeBtnList = modalDivList.item(0).getElementsByTagName('button');
        expect(closeBtnList.length).toBe(3);

        const errorFORMAT = modalDivList.item(0).getElementsByTagName('errorFORMAT');
        expect(errorFORMAT).toExist();
    });

    it('creates the component with a size error', () => {
        let thumbnail = "myThumnbnailUrl";
        let errors = ["SIZE"];
        let map = {
            thumbnail: thumbnail,
            id: 123,
            canWrite: true,
            errors: errors
        };

        const metadataModalItem = ReactDOM.render(<MetadataModal show={true} map={map} useModal={true} id="MetadataModal"/>, document.getElementById("container"));
        expect(metadataModalItem).toExist();

        const getModals = function() {
            return document.getElementsByTagName("body")[0].getElementsByClassName('modal-dialog');
        };

        expect(getModals().length).toBe(1);

        const modalDivList = document.getElementsByClassName("modal-content");
        const closeBtnList = modalDivList.item(0).getElementsByTagName('button');
        expect(closeBtnList.length).toBe(3);

        const errorFORMAT = modalDivList.item(0).getElementsByTagName('errorSIZE');
        expect(errorFORMAT).toExist();
    });

});
