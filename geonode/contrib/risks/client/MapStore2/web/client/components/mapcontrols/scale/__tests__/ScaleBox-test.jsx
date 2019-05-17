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
var ScaleBox = require('../ScaleBox');
var mapUtils = require('../../../../utils/MapUtils');

const TestUtils = require('react-addons-test-utils');

describe('ScaleBox', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });
    it('create component with defaults', () => {
        const sb = ReactDOM.render(<ScaleBox />, document.getElementById("container"));
        expect(sb).toExist();
        const domNode = ReactDOM.findDOMNode(sb);
        expect(domNode).toExist();
        expect(domNode.id).toBe('mapstore-scalebox');

        const comboItems = Array.prototype.slice.call(domNode.getElementsByTagName('option'), 0);
        expect(comboItems.length).toBe(29);

        expect(comboItems.reduce((pre, cur, i) => {
            const scale = parseInt(cur.innerHTML.replace(/1\s\:\s/i, ''), 10);
            const testScale = Math.round(mapUtils.getGoogleMercatorScale(i));
            return pre && (scale === testScale);
        }, true)).toBe(true);

        expect(comboItems.reduce((pre, cur, i) => {
            return pre && (i === 0 ? cur.selected : !cur.selected);
        }), true).toBe(true);
    });
    it('test handler for onChange event', () => {
        var newZoom;

        const sb = ReactDOM.render(<ScaleBox onChange={(z) => {newZoom = z; }}/>, document.getElementById("container"));
        expect(sb).toExist();
        const domNode = ReactDOM.findDOMNode(sb);
        expect(domNode).toExist();
        const domSelect = domNode.getElementsByTagName('select').item(0);
        expect(domSelect).toExist();

        domSelect.value = 5;
        TestUtils.Simulate.change(domSelect, {target: {value: 5}});
        expect(newZoom).toBe(5);
    });

    it('renders readOnly', () => {
        const sb = ReactDOM.render(<ScaleBox readOnly/>, document.getElementById("container"));
        expect(sb).toExist();
        const domNode = ReactDOM.findDOMNode(sb);
        expect(domNode).toExist();
        const domLabel = domNode.getElementsByTagName('label').item(0);
        expect(domLabel).toExist();
    });

    it('uses template', () => {
        const sb = ReactDOM.render(<ScaleBox readOnly template={(scale) => {
            return "Scale:" + scale;
        }}/>, document.getElementById("container"));
        expect(sb).toExist();
        const domNode = ReactDOM.findDOMNode(sb);
        expect(domNode).toExist();
        const domLabel = domNode.getElementsByTagName('label').item(0);
        expect(domLabel).toExist();
        expect(domLabel.innerHTML).toContain("Scale:");
    });
});
