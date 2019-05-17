/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var ReactDOM = require('react-dom');
var WMSLegend = require('../WMSLegend');

var expect = require('expect');

describe('test WMSLegend module component', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('tests WMSLegend component creation', () => {
        const l = {
            name: 'layer00',
            title: 'Layer',
            visibility: true,
            storeIndex: 9,
            type: 'wms',
            url: 'fakeurl'
        };
        const comp = ReactDOM.render(<WMSLegend node={l} />, document.getElementById("container"));

        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toExist();

        const image = domNode.getElementsByTagName('img');
        expect(image).toExist();
        expect(image.length).toBe(1);
    });

    it('tests WMSLegend is not shown if node is not visible', () => {
        const l = {
            name: 'layer00',
            title: 'Layer',
            visibility: false,
            storeIndex: 9,
            type: 'wms',
            url: 'fakeurl'
        };
        const comp = ReactDOM.render(<WMSLegend node={l} showOnlyIfVisible={true} />, document.getElementById("container"));

        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toNotExist();
    });
});
