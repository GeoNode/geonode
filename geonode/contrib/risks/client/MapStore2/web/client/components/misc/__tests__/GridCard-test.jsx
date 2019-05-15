/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactDOM = require('react-dom');
const GridCard = require('../GridCard.jsx');
const expect = require('expect');

const TestUtils = require('react-addons-test-utils');

describe('This test for GridCard', () => {
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
        const item = ReactDOM.render(<GridCard />, document.getElementById("container"));
        expect(item).toExist();

        const mapItemDom = ReactDOM.findDOMNode(item);
        expect(mapItemDom).toExist();

        expect(mapItemDom.className).toBe('gridcard');
        const headings = mapItemDom.getElementsByClassName('gridcard-title');
        expect(headings.length).toBe(1);
    });
    // test DEFAULTS
    it('creates the component with data', () => {
        const testName = "test";
        const testDescription = "testDescription";
        const item = ReactDOM.render(<GridCard header={testName}>{testDescription}</GridCard>, document.getElementById("container"));
        expect(item).toExist();

        const itemDom = ReactDOM.findDOMNode(item);
        expect(itemDom).toExist();

        expect(itemDom.className).toBe('gridcard');
        const headings = itemDom.getElementsByClassName('gridcard-title');
        expect(headings.length).toBe(1);
        expect(headings[0].innerHTML).toBe(testName);
    });

    it('test actions', () => {
        const testName = "test";
        const testDescription = "testDescription";
        var component = TestUtils.renderIntoDocument(<GridCard header={testName} actions={[{glyph: "test", onClick: () => {}}]}>{testDescription}></GridCard>);
        var button = TestUtils.findRenderedDOMComponentWithTag(
           component, 'button'
        );
        expect(button).toExist();
    });
});
