/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactDOM = require('react-dom');

const DefaultViewer = require('../DefaultViewer.jsx');

const expect = require('expect');

describe('DefaultViewer', () => {

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates the DefaultViewer component with defaults', () => {
        const viewer = ReactDOM.render(
            <DefaultViewer/>,
            document.getElementById("container")
        );

        expect(viewer).toExist();
    });

    it('creates the DefaultViewer component with custom container', () => {
        const Container = () => <div className="mycontainer"/>;
        const viewer = ReactDOM.render(
            <DefaultViewer container={Container}/>,
            document.getElementById("container")
        );

        expect(viewer).toExist();
        const dom = ReactDOM.findDOMNode(viewer);
        expect(dom.getElementsByClassName("mycontainer").length).toBe(1);
    });

    it('creates the DefaultViewer component with custom header', () => {
        const responses = [{
            response: "A",
            layerMetadata: {
                title: 'a'
            }
        }];
        const Header = () => <div className="mycontainer"/>;
        const viewer = ReactDOM.render(
            <DefaultViewer responses={responses} header={Header}/>,
            document.getElementById("container")
        );

        expect(viewer).toExist();
        const dom = ReactDOM.findDOMNode(viewer);
        expect(dom.getElementsByClassName("mycontainer").length).toBe(1);
    });

    it('creates the DefaultViewer component with custom validator', () => {
        const validator = () => ({
            getValidResponses: () => [{
                response: "A",
                layerMetadata: {
                    title: 'a'
                }
            }, {
                response: "B",
                layerMetadata: {
                    title: 'b'
                }
            }],
            getNoValidResponses: () => [{
                response: "C",
                layerMetadata: {
                    title: 'c'
                }
            }]
        });
        const viewer = ReactDOM.render(
            <DefaultViewer validator={validator}/>,
            document.getElementById("container")
        );

        expect(viewer).toExist();
        const dom = ReactDOM.findDOMNode(viewer);
        expect(dom.getElementsByClassName("panel").length).toBe(2);
        expect(dom.getElementsByClassName("alert").length).toBe(1);
    });

    it('creates the DefaultViewer component with no results', () => {
        const viewer = ReactDOM.render(
            <DefaultViewer/>,
            document.getElementById("container")
        );

        expect(viewer).toExist();
        const dom = ReactDOM.findDOMNode(viewer);
        expect(dom.getElementsByClassName("alert").length).toBe(1);
    });

    it('creates the DefaultViewer component with some results', () => {
        const responses = [{
            response: "A",
            layerMetadata: {
                title: 'a'
            }
        }, {
            response: "B",
            layerMetadata: {
                title: 'b'
            }
        }];
        const viewer = ReactDOM.render(
            <DefaultViewer responses={responses}/>,
            document.getElementById("container")
        );

        expect(viewer).toExist();
        const dom = ReactDOM.findDOMNode(viewer);
        expect(dom.getElementsByClassName("alert").length).toBe(0);
    });

    it('creates the DefaultViewer component with missing results', () => {
        const viewer = ReactDOM.render(
            <DefaultViewer missingResponses={1}/>,
            document.getElementById("container")
        );

        expect(viewer).toExist();
        const dom = ReactDOM.findDOMNode(viewer);
        expect(dom.getElementsByClassName("alert").length).toBe(0);
    });

    it('creates the DefaultViewer component with custom viewer', () => {
        const responses = [{
            response: "myresponse",
            layerMetadata: {
                title: 'a'
            }
        }];
        const viewers = {
            "custom": (props) => <span className="custom">{props.response}</span>
        };
        const viewer = ReactDOM.render(
            <DefaultViewer responses={responses} viewers={viewers} format="custom"/>,
            document.getElementById("container")
        );

        expect(viewer).toExist();
        const dom = ReactDOM.findDOMNode(viewer);
        expect(dom.getElementsByClassName("custom").length).toBe(1);
        expect(dom.innerHTML.indexOf('myresponse') !== -1).toBe(true);
    });
});
