/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');

var React = require('react');
var ReactDOM = require('react-dom');
var NominatimResultList = require('../NominatimResultList');
var NominatimResult = require('../NominatimResult');
const TestUtils = require('react-addons-test-utils');

describe("test the NominatimResultList", () => {
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
        var results = [{
            osm_id: 1,
            display_name: "Name",
            boundingbox: []
        }];
        const tb = ReactDOM.render(<NominatimResultList results={results}/>, document.getElementById("container"));
        expect(tb).toExist();

    });

    it('create component without items', () => {
        const tb = ReactDOM.render(<NominatimResultList />, document.getElementById("container"));
        expect(tb).toExist();
    });

    it('create component with empty items array', () => {
        const tb = ReactDOM.render(<NominatimResultList results={[]} notFoundMessage="not found"/>, document.getElementById("container"));
        expect(tb).toExist();
    });

    it('test click handler', () => {
        const testHandlers = {
            clickHandler: () => {},
            afterClick: () => {}
        };
        var items = [{
            osm_id: 1,
            display_name: "Name",
            boundingbox: [1, 2, 3, 4]
        }];
        const spy = expect.spyOn(testHandlers, 'clickHandler');
        var tb = ReactDOM.render(<NominatimResultList results={items} mapConfig={{size: 100, projection: "EPSG:4326"}}
            onItemClick={testHandlers.clickHandler}
            afterItemClick={testHandlers.afterItemClick}/>, document.getElementById("container"));
        let elem = TestUtils.scryRenderedComponentsWithType(tb, NominatimResult);
        expect(elem.length).toBe(1);

        let elem1 = TestUtils.findRenderedDOMComponentWithClass(elem[0], "search-result");
        ReactDOM.findDOMNode(elem1).click();
        expect(spy.calls.length).toEqual(1);
    });
});
