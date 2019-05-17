/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var expect = require('expect');
var ReactDOM = require('react-dom');
var Template = require('../Template');

describe("Test JSX Template", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('Test Template render jsx string', () => {
        let comp = ReactDOM.render(
            <Template template="<div id='template'/>"/>, document.getElementById("container"));
        expect(comp).toExist();
        const cmpDom = document.getElementById("template");
        expect(cmpDom).toExist();
        expect(cmpDom.id).toExist();
        expect(cmpDom.id).toBe("template");
    });
    it('Test Template render jsx as functipn', () => {
        let comp = ReactDOM.render(
            <Template
                template={ () => { return "<div id='template'/>"; } } />, document.getElementById("container"));
        expect(comp).toExist();
        const cmpDom = document.getElementById("template");
        expect(cmpDom).toExist();
        expect(cmpDom.id).toExist();
        expect(cmpDom.id).toBe("template");
    });
    it('Test Template render jsx string with model substitution', () => {
        let comp = ReactDOM.render(
            <Template template="<div id={model.id}/>" model={{id: "template"}} />
            , document.getElementById("container"));
        expect(comp).toExist();
        const cmpDom = document.getElementById("template");
        expect(cmpDom).toExist();
        expect(cmpDom.id).toExist();
        expect(cmpDom.id).toBe("template");
    });
    it('Test Template update', () => {
        let comp = ReactDOM.render(
            <Template template="<div id={model.id}/>" model={{id: "template"}} />
            , document.getElementById("container"));
        expect(comp).toExist();
        let cmpDom = document.getElementById("template");
        expect(cmpDom).toExist();
        expect(cmpDom.id).toExist();
        expect(cmpDom.id).toBe("template");
        comp = ReactDOM.render(
            <Template template="<div id={model.id}/>" model={{id: "template-update"}} />
            , document.getElementById("container"));
        cmpDom = document.getElementById("template-update");
        expect(cmpDom).toExist();
        expect(cmpDom.id).toExist();
        expect(cmpDom.id).toBe("template-update");
    });
    it('Test Template update template', () => {
        let comp = ReactDOM.render(
            <Template template="<div id={model.id}/>" model={{id: "temp"}} />
            , document.getElementById("container"));
        expect(comp).toExist();
        let cmpDom = document.getElementById("temp");
        expect(cmpDom).toExist();
        comp = ReactDOM.render(
            <Template template="<div id='template'/>" model={{id: "temp"}} />
            , document.getElementById("container"));
        cmpDom = document.getElementById("template");
        expect(cmpDom).toExist();
    });
});
