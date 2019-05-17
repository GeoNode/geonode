/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');

var React = require('react');
var ReactDOM = require('react-dom');
var SearchResult = require('../SearchResult');
const TestUtils = require('react-addons-test-utils');
const item = {
    properties: {
        prop1: 1,
        prop2: 2
    }
};
describe("test the NominatimResult", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('test component creation', () => {
        const tb = ReactDOM.render(<SearchResult item={item}/>, document.getElementById("container"));
        expect(tb).toExist();

    });

    it('create component without item', () => {
        const tb = ReactDOM.render(<SearchResult />, document.getElementById("container"));
        expect(tb).toExist();
    });

    it('create component with displayName and subtitle', () => {
        const tb = ReactDOM.render(<SearchResult item={item} displayName="test ${properties.prop1}" subTitle="test ${properties.prop2}"/>, document.getElementById("container"));
        expect(tb).toExist();
        const title = TestUtils.findRenderedDOMComponentWithClass(tb, "text-result-title");
        const subTitle = TestUtils.findRenderedDOMComponentWithClass(tb, "text-info");

        expect(title).toExist();
        expect(subTitle).toExist();
        expect(title.textContent).toBe("test 1");
        expect(subTitle.textContent).toBe("test 2");
    });

    it('test click handler', () => {
        const testHandlers = {
            clickHandler: (pressed) => {return pressed; }
        };
        const spy = expect.spyOn(testHandlers, 'clickHandler');
        var tb = ReactDOM.render(<SearchResult item={item} onItemClick={testHandlers.clickHandler}/>, document.getElementById("container"));
        let elem = TestUtils.findRenderedDOMComponentWithClass(tb, "search-result");
        expect(elem).toExist();
        ReactDOM.findDOMNode(elem).click();
        expect(spy.calls.length).toEqual(1);
    });
});
